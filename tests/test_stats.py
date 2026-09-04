"""Statistics tests."""
import json
from datetime import date

from app.services import plan_loader, stats, workout

START = date(2026, 9, 7)


def test_stats_empty(db):
    summary = stats.summary(db, "Asia/Shanghai", START)
    assert summary["total_completed"] == 0
    assert summary["pullup_total"] == 0
    assert summary["pullup_max"] == 0
    assert summary["run_total_km"] == 0


def test_pullup_stats(db):
    program = plan_loader.load_program()
    day, _, _ = workout.get_or_create_workout_day(db, START, program, START)
    pullup = next(log for log in day.logs if log.exercise_key == "pullup")
    pullup.actual_reps = json.dumps([5, 5, 4, 3])
    pullup.completed = True
    workout.recompute_status(day)
    db.commit()

    summary = stats.summary(db, "Asia/Shanghai", START)
    assert summary["pullup_total"] == 17
    assert summary["pullup_max"] == 5


def test_run_stats(db):
    program = plan_loader.load_program()
    saturday = date(2026, 9, 12)
    day, _, _ = workout.get_or_create_workout_day(db, saturday, program, START)
    run = next(log for log in day.logs if log.exercise_key == "endurance_run")
    run.actual_distance_meters = 3000
    run.actual_duration_seconds = 1500
    run.completed = True
    workout.recompute_status(day)
    db.commit()

    summary = stats.summary(db, "Asia/Shanghai", START)
    assert summary["run_total_km"] == 3.0
    assert summary["run_longest_km"] == 3.0
    assert summary["best_5k_seconds"] is None  # under 5km


def test_completed_count(db):
    program = plan_loader.load_program()
    day, _, _ = workout.get_or_create_workout_day(db, START, program, START)
    for log in day.logs:
        log.completed = True
    workout.recompute_status(day)
    db.commit()

    summary = stats.summary(db, "Asia/Shanghai", START)
    assert summary["total_completed"] == 1
