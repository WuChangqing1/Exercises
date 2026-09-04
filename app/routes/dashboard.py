"""Training dashboard (today's workout)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.helpers import day_card_context, get_tz
from app.security import require_user
from app.services import schedule
from app.templating import templates

router = APIRouter(prefix="/training", tags=["dashboard"])


@router.get("/")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    tz = get_tz(db)
    today = schedule.today_in_tz(tz)
    ctx = day_card_context(db, today)
    ctx.update(
        {
            "today": today,
            "active_page": "dashboard",
        }
    )
    return templates.TemplateResponse(request, "dashboard.html", ctx)
