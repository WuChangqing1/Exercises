"""Workout-day materialization, status computation, and log updates.

Day statuses (canonical):
- exercised   — at least one activity is checked: the user exercised that day.
- missed      — the user explicitly recorded that they did NOT exercise (reason optional).
- unrecorded  — the day exists but no decision has been recorded yet.

The recommended plan is shown purely as a reference; the user checks whatever
they actually did, and can add their own activities.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ExerciseLog, WorkoutDay
from app.services import plan_loader, schedule

CUSTOM_KEY = "custom"

_EXERCISED_LEGACY = {"partial", "completed", "exercised"}
_MISSED_LEGACY = {"skipped"}


def effective_status(day: WorkoutDay) -> str:
    """Canonical status for display/logic; normalizes any legacy status strings."""
    s = day.status
    if s == "missed" or s in _MISSED_LEGACY:
        return "missed"
    if s in _EXERCISED_LEGACY:
        return "exercised"
    if any(log.completed for log in day.logs):
        return "exercised"
    return "unrecorded"


def recompute_status(day: WorkoutDay) -> str:
    """Persist status derived from the checked activities (after any change)."""
    has_any = any(log.completed for log in day.logs)
    status = "exercised" if has_any else "unrecorded"
    if status == "exercised":
        if day.status == "missed":
            day.skip_reason = None
        if not day.completed_at:
            day.completed_at = datetime.utcnow()
    day.status = status
    return status


def get_or_create_workout_day(
    db: Session,
    target: date,
    program: dict[str, Any],
    start_date: date,
) -> tuple[WorkoutDay, dict[str, Any], bool]:
    """Return (workout_day, day_plan, finished), creating rows on first access."""
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
        status="unrecorded",
    )
    db.add(day)
    db.flush()

    # Seed the recommended activities as optional, unchecked rows.
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


def toggle_log(db: Session, day: WorkoutDay, log: ExerciseLog) -> WorkoutDay:
    """Check/uncheck one activity; the day becomes exercised when any is checked."""
    log.completed = not log.completed
    log.completed_at = datetime.utcnow() if log.completed else None
    recompute_status(day)
    db.commit()
    db.refresh(day)
    return day


def mark_missed(db: Session, day: WorkoutDay, reason: str | None) -> WorkoutDay:
    """Record that the user did not exercise on this day."""
    day.status = "missed"
    day.skip_reason = reason or None
    db.commit()
    db.refresh(day)
    return day


def add_custom_log(
    db: Session, day: WorkoutDay, name: str, note: str | None = None
) -> ExerciseLog:
    """Record an activity the user did that is not part of the recommendation."""
    log = ExerciseLog(
        workout_day_id=day.id,
        exercise_key=CUSTOM_KEY,
        planned_name=(name or "").strip()[:128],
        note=note or None,
        completed=True,
        completed_at=datetime.utcnow(),
    )
    db.add(log)
    db.flush()
    db.expire(day, ["logs"])
    recompute_status(day)
    db.commit()
    db.refresh(day)
    db.refresh(log)
    return log


def delete_log(db: Session, day: WorkoutDay, log: ExerciseLog) -> WorkoutDay:
    """Remove a (custom) activity record from the day."""
    db.delete(log)
    db.flush()
    db.expire(day, ["logs"])
    recompute_status(day)
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
        "status": effective_status(day),
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
