"""Statistics page."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.helpers import get_tz
from app.security import require_user
from app.services import schedule, stats
from app.templating import templates

router = APIRouter(prefix="/training", tags=["stats"])


@router.get("/stats")
def stats_page(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    tz = get_tz(db)
    today = schedule.today_in_tz(tz)
    summary = stats.summary(db, tz, today)
    charts = stats.chart_data(db)
    return templates.TemplateResponse(
        request,
        "stats.html",
        {
            "summary": summary,
            "charts": charts,
            "fmt_duration": stats.format_duration,
            "active_page": "stats",
        },
    )
