"""Shared helpers for training routes."""
from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AppSettings
from app.services import plan_loader, schedule, workout

STATUS_META = {
    "exercised": {"label": "运动了", "symbol": "✓", "css": "status-exercised"},
    "missed": {"label": "没运动", "symbol": "×", "css": "status-missed"},
    "unrecorded": {"label": "未记录", "symbol": "○", "css": "status-unrecorded"},
}


def get_or_create_settings(db: Session) -> AppSettings:
    settings_row = db.scalar(select(AppSettings).limit(1))
    if settings_row is None:
        settings_row = AppSettings()
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return settings_row


def get_tz(db: Session) -> str:
    return get_or_create_settings(db).timezone


def get_start_date(db: Session) -> date:
    return schedule.parse_iso_date(get_or_create_settings(db).program_start_date)


def day_card_context(db: Session, target: date) -> dict[str, Any]:
    settings_row = get_or_create_settings(db)
    start = schedule.parse_iso_date(settings_row.program_start_date)
    program = plan_loader.load_program()
    day, plan, finished = workout.get_or_create_workout_day(db, target, program, start)
    today = schedule.today_in_tz(settings_row.timezone)

    status = workout.effective_status(day)
    plan_map = {ex.get("key"): ex for ex in plan.get("exercises", []) if isinstance(ex, dict)}

    return {
        "day": day,
        "plan": plan,
        "plan_map": plan_map,
        "finished": finished,
        "target": target,
        "is_today": target == today,
        "status": status,
        "status_meta": STATUS_META,
        "has_checked": any(log.completed for log in day.logs),
        "suggested_rest": bool(plan.get("rest", False)),
    }
