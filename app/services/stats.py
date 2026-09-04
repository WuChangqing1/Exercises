"""Statistics derived from workout and exercise logs."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ExerciseLog, WorkoutDay

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
    return list(db.scalars(select(WorkoutDay).order_by(WorkoutDay.date)).all())


def _all_logs(db: Session) -> list[ExerciseLog]:
    return list(db.scalars(select(ExerciseLog)).all())


def _iso_week(d: date) -> str:
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def _week_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _sum_reps(logs: list[ExerciseLog], keys: set[str]) -> int:
    total = 0
    for log in logs:
        if log.exercise_key in keys:
            total += sum(_parse_reps(log.actual_reps))
    return total


def summary(db: Session, tz: str, today: date) -> dict[str, Any]:
    days = _all_days(db)
    logs = _all_logs(db)

    # Group days by ISO week.
    weeks: dict[str, list[WorkoutDay]] = defaultdict(list)
    for day in days:
        weeks[_iso_week(date.fromisoformat(day.date))].append(day)

    monday = _week_monday(today)
    this_week_key = _iso_week(monday)

    def week_complete(days_in_week: list[WorkoutDay]) -> bool:
        non_rest = [d for d in days_in_week if d.status != "rest"]
        return len(non_rest) > 0 and all(d.status == "completed" for d in non_rest)

    # Consecutive completed weeks.
    consecutive = 0
    ordered_weeks = sorted(weeks.keys(), reverse=True)
    for key in ordered_weeks:
        complete = week_complete(weeks[key])
        if complete:
            consecutive += 1
        elif key == this_week_key:
            continue  # current (incomplete) week doesn't break the streak
        else:
            break

    # This-week completion rate (non-rest days up to today).
    this_week_days = [
        d for d in days if _iso_week(date.fromisoformat(d.date)) == this_week_key
    ]
    eligible = [d for d in this_week_days if d.status != "rest" and d.date <= today.isoformat()]
    completion_rate = 0.0
    if eligible:
        points = sum(
            1 if d.status == "completed" else 0.5 if d.status == "partial" else 0
            for d in eligible
        )
        completion_rate = round(points / len(eligible) * 100, 1)

    total_completed = sum(1 for d in days if d.status == "completed")

    pullup_total = _sum_reps(logs, _PULLUP_KEYS)
    pullup_max = 0
    plank_max = 0
    total_run_m = 0.0
    longest_run_m = 0.0
    best_5k_seconds: int | None = None
    this_week_run_m = 0.0

    for log in logs:
        if log.exercise_key in _PULLUP_KEYS:
            reps = _parse_reps(log.actual_reps)
            if reps:
                pullup_max = max(pullup_max, max(reps))
        if log.exercise_key == "plank":
            plank_max = max(plank_max, log.actual_duration_seconds or 0)
        if log.exercise_key in _RUN_KEYS:
            dist = float(log.actual_distance_meters or 0)
            total_run_m += dist
            longest_run_m = max(longest_run_m, dist)
            log_week = _iso_week(date.fromisoformat(log.workout_day.date))
            if log_week == this_week_key:
                this_week_run_m += dist
            if dist >= 4900 and log.actual_duration_seconds:
                if best_5k_seconds is None or log.actual_duration_seconds < best_5k_seconds:
                    best_5k_seconds = log.actual_duration_seconds

    return {
        "completion_rate_this_week": completion_rate,
        "total_completed": total_completed,
        "consecutive_completed_weeks": consecutive,
        "pullup_total": pullup_total,
        "pullup_max": pullup_max,
        "plank_max_seconds": plank_max,
        "run_this_week_km": round(this_week_run_m / 1000, 2),
        "run_total_km": round(total_run_m / 1000, 2),
        "run_longest_km": round(longest_run_m / 1000, 2),
        "best_5k_seconds": best_5k_seconds,
    }


def chart_data(db: Session) -> dict[str, Any]:
    """Series for Chart.js: weekly completion rate, pull-up max, run volume."""
    days = _all_days(db)
    logs = _all_logs(db)

    weeks: dict[str, list[WorkoutDay]] = defaultdict(list)
    for day in days:
        weeks[_iso_week(date.fromisoformat(day.date))].append(day)

    log_weeks: dict[str, list[ExerciseLog]] = defaultdict(list)
    for log in logs:
        log_weeks[_iso_week(date.fromisoformat(log.workout_day.date))].append(log)

    keys = sorted(set(weeks) | set(log_weeks))
    labels = [k.replace("-W", " W") for k in keys]

    completion = []
    pullup_max = []
    run_km = []

    for key in keys:
        week_days = weeks.get(key, [])
        non_rest = [d for d in week_days if d.status != "rest"]
        if non_rest:
            points = sum(
                1 if d.status == "completed" else 0.5 if d.status == "partial" else 0
                for d in non_rest
            )
            completion.append(round(points / len(non_rest) * 100, 1))
        else:
            completion.append(0)

        wk_logs = log_weeks.get(key, [])
        best = 0
        for log in wk_logs:
            if log.exercise_key in _PULLUP_KEYS:
                reps = _parse_reps(log.actual_reps)
                if reps:
                    best = max(best, max(reps))
        pullup_max.append(best)

        run_m = sum(
            float(log.actual_distance_meters or 0)
            for log in wk_logs
            if log.exercise_key in _RUN_KEYS
        )
        run_km.append(round(run_m / 1000, 2))

    return {
        "labels": labels,
        "completion": completion,
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
