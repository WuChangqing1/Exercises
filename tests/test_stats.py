"""Statistics tests (day-based: exercised days, streaks)."""
import json
from datetime import date, timedelta

from app.services import plan_loader, stats, workout

START = date(2026, 9, 7)  # Monday


def _materialize(db, target, complete: bool):
    program = plan_loader.load_program()
    day, _, _ = workout.get_or_create_workout_day(db, target, program, START)
    if complete:
        workout.toggle_log(db, day, day.logs[0])  # any single check marks exercised
    return day


def _exercise_via_custom(db, target):
    """Exercise on any day (incl. plan rest days) by recording a custom activity."""
    program = plan_loader.load_program()
    day, _, _ = workout.get_or_create_workout_day(db, target, program, START)
    workout.add_custom_log(db, day, "散步 30 分钟")
    return day


def test_stats_empty(db):
    summary = stats.summary(db, "Asia/Shanghai", START)
    assert summary["total_exercised"] == 0
    assert summary["streak"] == 0
    assert summary["this_week"] == 0
    assert summary["this_month"] == 0


def test_total_and_streak(db):
    _exercise_via_custom(db, START)                        # Mon
    _materialize(db, START + timedelta(days=1), True)      # Tue
    today = START + timedelta(days=2)                      # Wed (rest day → custom)
    _exercise_via_custom(db, today)

    summary = stats.summary(db, "Asia/Shanghai", today)
    assert summary["total_exercised"] == 3
    assert summary["streak"] == 3
    assert summary["this_week"] == 3
    assert summary["this_month"] == 3


def test_missed_day_breaks_streak(db):
    _materialize(db, START, True)  # Mon
    program = plan_loader.load_program()
    tue, _, _ = workout.get_or_create_workout_day(db, START + timedelta(days=1), program, START)
    workout.mark_missed(db, tue, "太忙")   # Tue missed
    today = START + timedelta(days=3)      # Thu
    _materialize(db, today, True)

    summary = stats.summary(db, "Asia/Shanghai", today)
    assert summary["total_exercised"] == 2
    assert summary["streak"] == 1


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

    summary = stats.summary(db, "Asia/Shanghai", saturday)
    assert summary["run_total_km"] == 3.0
    assert summary["run_longest_km"] == 3.0
    assert summary["best_5k_seconds"] is None  # under 5km


def test_chart_data_exercised_counts(db):
    _materialize(db, START, True)
    _materialize(db, START + timedelta(days=1), False)
    charts = stats.chart_data(db)
    assert charts["labels"] == ["2026 W37"]
    assert charts["exercised"] == [1]
