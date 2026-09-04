"""Workout materialization and status transition tests."""
import json
from datetime import date

from app.services import plan_loader, workout

START = date(2026, 9, 7)  # Monday


def test_materialize_monday(db):
    program = plan_loader.load_program()
    day, plan, finished = workout.get_or_create_workout_day(db, START, program, START)
    assert finished is False
    assert day.status == "not_started"
    assert plan["type"] == "背部 + 核心"
    assert len(day.logs) == 7


def test_materialize_is_idempotent(db):
    program = plan_loader.load_program()
    workout.get_or_create_workout_day(db, START, program, START)
    day, _, _ = workout.get_or_create_workout_day(db, START, program, START)
    assert len(day.logs) == 7


def test_toggle_partial_then_complete(db):
    program = plan_loader.load_program()
    day, _, _ = workout.get_or_create_workout_day(db, START, program, START)

    workout.toggle_log(db, day, day.logs[0])
    assert day.status == "partial"
    assert day.logs[0].completed is True

    for log in day.logs[1:]:
        workout.toggle_log(db, day, log)
    assert day.status == "completed"
    assert day.completed_at is not None


def test_skip_and_unskip(db):
    program = plan_loader.load_program()
    day, _, _ = workout.get_or_create_workout_day(db, START, program, START)

    workout.skip_day(db, day, "太忙")
    assert day.status == "skipped"
    assert day.skip_reason == "太忙"

    workout.toggle_log(db, day, day.logs[0])
    assert day.status == "partial"


def test_rest_day(db):
    program = plan_loader.load_program()
    day, plan, _ = workout.get_or_create_workout_day(db, date(2026, 9, 9), program, START)
    assert plan["rest"] is True
    assert day.status == "rest"
    assert len(day.logs) == 0


def test_dashboard_page_renders(logged_in_client):
    resp = logged_in_client.get("/training/")
    assert resp.status_code == 200
    assert "Training" in resp.text


def test_actual_reps_json_roundtrip(db):
    program = plan_loader.load_program()
    day, _, _ = workout.get_or_create_workout_day(db, START, program, START)
    pullup = next(log for log in day.logs if log.exercise_key == "pullup")
    workout.update_log_details(db, pullup, {"actual_reps": json.dumps([5, 5, 4, 3]), "rpe": 8})
    db.refresh(pullup)
    assert json.loads(pullup.actual_reps) == [5, 5, 4, 3]
    assert pullup.rpe == 8
