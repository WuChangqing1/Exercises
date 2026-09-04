"""Data export: full JSON plus workout/exercise CSVs."""
from __future__ import annotations

import csv
import io
import json
from typing import Any

from sqlalchemy.orm import Session

from app.models import ExerciseLog, WorkoutDay
from app.services.workout import serialize_day


def export_json(db: Session) -> str:
    days = db.query(WorkoutDay).order_by(WorkoutDay.date).all()
    payload: dict[str, Any] = {
        "version": 1,
        "workout_days": [serialize_day(day) for day in days],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def export_workout_csv(db: Session) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["date", "week_number", "day_type", "status", "skip_reason", "note", "completed_at"]
    )
    for day in db.query(WorkoutDay).order_by(WorkoutDay.date).all():
        writer.writerow(
            [
                day.date,
                day.week_number,
                day.day_type,
                day.status,
                day.skip_reason or "",
                day.note or "",
                day.completed_at.isoformat() if day.completed_at else "",
            ]
        )
    return buffer.getvalue()


def export_exercise_csv(db: Session) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "date",
            "exercise_key",
            "planned_name",
            "planned_sets",
            "planned_reps",
            "planned_duration",
            "planned_distance",
            "completed",
            "actual_sets",
            "actual_reps",
            "actual_duration_seconds",
            "actual_distance_meters",
            "rpe",
            "note",
        ]
    )
    rows = (
        db.query(ExerciseLog)
        .join(WorkoutDay, ExerciseLog.workout_day_id == WorkoutDay.id)
        .order_by(WorkoutDay.date, ExerciseLog.id)
        .all()
    )
    for log in rows:
        writer.writerow(
            [
                log.workout_day.date,
                log.exercise_key,
                log.planned_name,
                log.planned_sets or "",
                log.planned_reps or "",
                log.planned_duration or "",
                log.planned_distance or "",
                "1" if log.completed else "0",
                log.actual_sets or "",
                log.actual_reps or "",
                log.actual_duration_seconds or "",
                log.actual_distance_meters or "",
                log.rpe or "",
                log.note or "",
            ]
        )
    return buffer.getvalue()
