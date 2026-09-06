"""Calendar: month view with per-day status and a selected day card."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import WorkoutDay
from app.routes.helpers import day_card_context, get_tz
from app.security import require_user
from app.services import schedule, workout
from app.templating import templates

router = APIRouter(prefix="/training", tags=["calendar"])


def build_month_grid(year: int, month: int, status_map: dict[str, str], today: date):
    first = date(year, month, 1)
    start = first - timedelta(days=first.weekday())  # Monday of the containing week
    grid = []
    for week in range(6):
        row = []
        for i in range(7):
            d = start + timedelta(days=week * 7 + i)
            row.append(
                {
                    "date": d.isoformat(),
                    "day": d.day,
                    "in_month": d.month == month,
                    "status": status_map.get(d.isoformat(), "unrecorded"),
                    "is_today": d == today,
                }
            )
        grid.append(row)
    return grid


@router.get("/calendar")
def calendar_page(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_user),
    day: str | None = None,
):
    tz = get_tz(db)
    today = schedule.today_in_tz(tz)
    selected = date.fromisoformat(day) if day else today

    days = list(db.scalars(select(WorkoutDay).options(selectinload(WorkoutDay.logs))).all())
    status_map = {d.date: workout.effective_status(d) for d in days}

    ctx = day_card_context(db, selected)
    ctx.update(
        {
            "grid": build_month_grid(selected.year, selected.month, status_map, today),
            "month_label": f"{selected.year}年{selected.month}月",
            "selected": selected,
            "today": today,
            "prev_month": date(selected.year, selected.month, 1) - timedelta(days=1),
            "next_month": date(selected.year, selected.month, 28) + timedelta(days=7),
            "active_page": "calendar",
        }
    )
    return templates.TemplateResponse(request, "calendar.html", ctx)
