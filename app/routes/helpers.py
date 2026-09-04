"""Shared helpers for training routes."""
from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AppSettings
from app.services import plan_loader, schedule, workout

STATUS_META = {
    "not_started": {"label": "未开始", "symbol": "○", "css": "status-not-started"},
    "partial": {"label": "部分完成", "symbol": "△", "css": "status-partial"},
    "completed": {"label": "完成", "symbol": "✓", "css": "status-completed"},
    "skipped": {"label": "跳过", "symbol": "×", "css": "status-skipped"},
    "rest": {"label": "休息", "symbol": "—", "css": "status-rest"},
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

    total = len(day.logs)
    done = sum(1 for log in day.logs if log.completed)
    pct = int(round(done / total * 100)) if total else 0

    plan_map = {ex.get("key"): ex for ex in plan.get("exercises", []) if isinstance(ex, dict)}

    return {
        "day": day,
        "plan": plan,
        "plan_map": plan_map,
        "finished": finished,
        "target": target,
        "is_today": target == today,
        "status_meta": STATUS_META,
        "progress_done": done,
        "progress_total": total,
        "progress_pct": pct,
    }
