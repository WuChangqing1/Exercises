"""Workout-day materialization, status computation, and log updates."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ExerciseLog, WorkoutDay
from app.services import plan_loader, schedule


def get_or_create_workout_day(
    db: Session,
    target: date,
    program: dict[str, Any],
    start_date: date,
) -> tuple[WorkoutDay, dict[str, Any], bool]:
    """Return (workout_day, day_plan, finished) creating rows on first access."""
    date_str = target.isoformat()
    day = db.scalar(select(WorkoutDay).where(WorkoutDay.date == date_str))
    if day is not None:
        plan = schedule.get_day_plan(program, target, day.week_number)
        _, finished = schedule.week_number(start_date, target, plan_loader.total_weeks(program))
        return day, plan, finished

    week, finished = schedule.week_number(start_date, target, plan_loader.total_weeks(program))
    plan = schedule.get_day_plan(program, target, week)

    day = WorkoutDay(
        date=date_str,
        week_number=week,
        day_type=plan["type"],
        status="rest" if plan["rest"] else "not_started",
    )
    db.add(day)
    db.flush()

    for ex in plan["exercises"]:
        log = ExerciseLog(
            workout_day_id=day.id,
            exercise_key=ex.get("key", ""),
            planned_name=ex.get("name", ""),
            planned_sets=ex.get("sets"),
            planned_reps=ex.get("reps"),
            planned_duration=ex.get("duration"),
            planned_distance=ex.get("distance"),
        )
        db.add(log)

    db.commit()
    db.refresh(day)
    return day, plan, finished


def recompute_status(day: WorkoutDay) -> str:
    """Derive status from exercise logs; called after any log change."""
    if day.status == "skipped":
        return "skipped"
    if day.status == "rest":
        return "rest"

    logs = day.logs
    if not logs:
        return "not_started"

    completed = sum(1 for log in logs if log.completed)
    if completed == 0:
        status = "not_started"
    elif completed == len(logs):
        status = "completed"
        day.completed_at = datetime.utcnow()
    else:
        status = "partial"
    day.status = status
    return status


def toggle_log(db: Session, day: WorkoutDay, log: ExerciseLog) -> WorkoutDay:
    log.completed = not log.completed
    log.completed_at = datetime.utcnow() if log.completed else None
    # Checking a box on a skipped day un-skips it.
    if day.status == "skipped":
        day.status = "not_started"
        day.skip_reason = None
    recompute_status(day)
    db.commit()
    db.refresh(day)
    return day


def skip_day(db: Session, day: WorkoutDay, reason: str | None) -> WorkoutDay:
    day.status = "skipped"
    day.skip_reason = reason or None
    db.commit()
    db.refresh(day)
    return day


def update_log_details(db: Session, log: ExerciseLog, data: dict[str, Any]) -> None:
    for field in (
        "actual_sets",
        "actual_reps",
        "actual_duration_seconds",
        "actual_distance_meters",
        "rpe",
        "note",
    ):
        if field in data:
            setattr(log, field, data[field])
    db.commit()


def serialize_day(day: WorkoutDay) -> dict[str, Any]:
    return {
        "id": day.id,
        "date": day.date,
        "week_number": day.week_number,
        "day_type": day.day_type,
        "status": day.status,
        "skip_reason": day.skip_reason,
        "note": day.note,
        "completed_at": day.completed_at.isoformat() if day.completed_at else None,
        "logs": [
            {
                "id": log.id,
                "exercise_key": log.exercise_key,
                "planned_name": log.planned_name,
                "planned_sets": log.planned_sets,
                "planned_reps": log.planned_reps,
                "planned_duration": log.planned_duration,
                "planned_distance": log.planned_distance,
                "completed": log.completed,
                "actual_sets": log.actual_sets,
                "actual_reps": log.actual_reps,
                "actual_duration_seconds": log.actual_duration_seconds,
                "actual_distance_meters": log.actual_distance_meters,
                "rpe": log.rpe,
                "note": log.note,
                "completed_at": log.completed_at.isoformat() if log.completed_at else None,
            }
            for log in day.logs
        ],
    }
