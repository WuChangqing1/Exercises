"""Daily exercise-record materialization and status tests (exercised/missed/unrecorded)."""
import json
from datetime import date

from app.services import plan_loader, workout

START = date(2026, 9, 7)  # Monday


def test_materialize_monday(db):
    program = plan_loader.load_program()
    day, plan, finished = workout.get_or_create_workout_day(db, START, program, START)
    assert finished is False
    assert day.status == "unrecorded"
    assert plan["type"] == "背部 + 核心"
    assert len(day.logs) == 7
    assert all(log.completed is False for log in day.logs)


def test_materialize_is_idempotent(db):
    program = plan_loader.load_program()
    workout.get_or_create_workout_day(db, START, program, START)
    day, _, _ = workout.get_or_create_workout_day(db, START, program, START)
    assert len(day.logs) == 7


def test_checking_any_activity_marks_exercised(db):
    program = plan_loader.load_program()
    day, _, _ = workout.get_or_create_workout_day(db, START, program, START)

    workout.toggle_log(db, day, day.logs[0])
    assert workout.effective_status(day) == "exercised"
    assert day.status == "exercised"
    assert day.logs[0].completed is True

    # Unticking everything returns the day to unrecorded.
    workout.toggle_log(db, day, day.logs[0])
    assert workout.effective_status(day) == "unrecorded"


def test_mark_missed_and_unmark(db):
    program = plan_loader.load_program()
    day, _, _ = workout.get_or_create_workout_day(db, START, program, START)

    workout.mark_missed(db, day, "太忙")
    assert workout.effective_status(day) == "missed"
    assert day.skip_reason == "太忙"

    # Checking an activity afterwards overrides the missed record.
    workout.toggle_log(db, day, day.logs[0])
    assert workout.effective_status(day) == "exercised"
    assert day.skip_reason is None


def test_add_and_delete_custom_activity(db):
    program = plan_loader.load_program()
    day, _, _ = workout.get_or_create_workout_day(db, START, program, START)

    log = workout.add_custom_log(db, day, "打羽毛球")
    assert log.exercise_key == workout.CUSTOM_KEY
    assert log.planned_name == "打羽毛球"
    assert log.completed is True
    assert workout.effective_status(day) == "exercised"

    workout.delete_log(db, day, log)
    assert workout.effective_status(day) == "unrecorded"
    assert len(day.logs) == 7


def test_rest_day(db):
    program = plan_loader.load_program()
    day, plan, _ = workout.get_or_create_workout_day(db, date(2026, 9, 9), program, START)
    assert plan["rest"] is True
    assert day.status == "unrecorded"
    assert len(day.logs) == 0


def test_effective_status_normalizes_legacy(db):
    program = plan_loader.load_program()

    def day_for(d: date) -> object:
        day, _, _ = workout.get_or_create_workout_day(db, d, program, START)
        return day

    day = day_for(START)
    day.status = "completed"  # legacy value
    assert workout.effective_status(day) == "exercised"

    day2 = day_for(date(2026, 9, 8))
    day2.status = "skipped"
    day2.skip_reason = "累了"
    assert workout.effective_status(day2) == "missed"

    day3 = day_for(date(2026, 9, 10))
    day3.status = "rest"
    assert workout.effective_status(day3) == "unrecorded"


def test_dashboard_page_renders(logged_in_client):
    resp = logged_in_client.get("/training/")
    assert resp.status_code == 200
    assert "Training" in resp.text


def test_main_pages_render(logged_in_client):
    for path in ("/training/", "/training/calendar", "/training/stats", "/training/settings"):
        resp = logged_in_client.get(path)
        assert resp.status_code == 200, path


def test_actual_reps_json_roundtrip(db):
    program = plan_loader.load_program()
    day, _, _ = workout.get_or_create_workout_day(db, START, program, START)
    pullup = next(log for log in day.logs if log.exercise_key == "pullup")
    workout.update_log_details(db, pullup, {"actual_reps": json.dumps([5, 5, 4, 3]), "rpe": 8})
    db.refresh(pullup)
    assert json.loads(pullup.actual_reps) == [5, 5, 4, 3]
    assert pullup.rpe == 8
