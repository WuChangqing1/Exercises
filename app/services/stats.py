"""Statistics derived from the daily exercise record.

Primary metrics are day-based ("did I exercise that day"), since the tracker
now records actual activity instead of plan completion. Pull-up / running
metrics are only shown when detailed records exist.
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import ExerciseLog, WorkoutDay
from app.services import workout

_RUN_KEYS = {"easy_run", "interval", "endurance_run"}
_PULLUP_KEYS = {"pullup", "chinup"}


def _parse_reps(value: str | None) -> list[int]:
    if not value:
        return []
    try:
        data = json.loads(value)
        if isinstance(data, list):
            return [int(x) for x in data if str(x).lstrip("-").isdigit()]
    except Exception:
        pass
    return []


def _all_days(db: Session) -> list[WorkoutDay]:
    return list(
        db.scalars(
            select(WorkoutDay)
            .options(selectinload(WorkoutDay.logs))
            .order_by(WorkoutDay.date)
        ).all()
    )


def _all_logs(db: Session) -> list[ExerciseLog]:
    return list(db.scalars(select(ExerciseLog)).all())


def _iso_week(d: date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def _exercised_dates(db: Session) -> set[str]:
    return {d.date for d in _all_days(db) if workout.effective_status(d) == "exercised"}


def _streak(exercised: set[str], today: date) -> int:
    """Consecutive exercised calendar days ending at today (or the latest past one)."""
    if not exercised:
        return 0
    d = today
    for _ in range(366):
        if d.isoformat() in exercised:
            break
        d -= timedelta(days=1)
    else:
        return 0
    count = 0
    while d.isoformat() in exercised:
        count += 1
        d -= timedelta(days=1)
    return count


def summary(db: Session, tz: str, today: date) -> dict[str, Any]:
    exercised = _exercised_dates(db)
    logs = _all_logs(db)

    total_exercised = len(exercised)
    streak = _streak(exercised, today)

    monday = today - timedelta(days=today.weekday())
    week_dates = {(monday + timedelta(days=i)).isoformat() for i in range(7)}
    this_week = len(exercised & week_dates)
    month_prefix = today.strftime("%Y-%m")
    this_month = sum(1 for d in exercised if d.startswith(month_prefix))

    pullup_total = 0
    pullup_max = 0
    run_total_m = 0.0
    longest_run_m = 0.0
    best_5k_seconds: int | None = None

    for log in logs:
        if log.exercise_key in _PULLUP_KEYS:
            reps = _parse_reps(log.actual_reps)
            if reps:
                pullup_total += sum(reps)
                pullup_max = max(pullup_max, max(reps))
        if log.exercise_key in _RUN_KEYS:
            dist = float(log.actual_distance_meters or 0)
            run_total_m += dist
            longest_run_m = max(longest_run_m, dist)
            if dist >= 4900 and log.actual_duration_seconds:
                if best_5k_seconds is None or log.actual_duration_seconds < best_5k_seconds:
                    best_5k_seconds = log.actual_duration_seconds

    return {
        "total_exercised": total_exercised,
        "streak": streak,
        "this_week": this_week,
        "this_month": this_month,
        "pullup_total": pullup_total,
        "pullup_max": pullup_max,
        "run_total_km": round(run_total_m / 1000, 2),
        "run_longest_km": round(longest_run_m / 1000, 2),
        "best_5k_seconds": best_5k_seconds,
    }


def chart_data(db: Session) -> dict[str, Any]:
    """Weekly exercised-day counts plus pull-up/run series when recorded."""
    days = _all_days(db)
    logs = _all_logs(db)

    week_exercised: dict[str, int] = defaultdict(int)
    for day in days:
        if workout.effective_status(day) == "exercised":
            week_exercised[_iso_week(date.fromisoformat(day.date))] += 1

    week_logs: dict[str, list[ExerciseLog]] = defaultdict(list)
    for log in logs:
        week_logs[_iso_week(date.fromisoformat(log.workout_day.date))].append(log)

    keys = sorted(set(week_exercised) | set(week_logs))
    labels = [k.replace("-W", " W") for k in keys]

    exercised = [week_exercised.get(k, 0) for k in keys]
    pullup_max = []
    run_km = []
    for key in keys:
        best = 0
        run_m = 0.0
        for log in week_logs.get(key, []):
            if log.exercise_key in _PULLUP_KEYS:
                reps = _parse_reps(log.actual_reps)
                if reps:
                    best = max(best, max(reps))
            if log.exercise_key in _RUN_KEYS:
                run_m += float(log.actual_distance_meters or 0)
        pullup_max.append(best)
        run_km.append(round(run_m / 1000, 2))

    return {
        "labels": labels,
        "exercised": exercised,
        "pullup_max": pullup_max,
        "run_km": run_km,
    }


def format_duration(seconds: int | None) -> str:
    if not seconds:
        return "—"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
