"""Training actions: checkbox toggle, skip, and detail edits."""
from __future__ import annotations

import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ExerciseLog
from app.routes.helpers import day_card_context, get_start_date, get_tz
from app.security import require_user, verify_csrf
from app.services import plan_loader, schedule, workout
from app.templating import templates

router = APIRouter(prefix="/training", tags=["training"])


def _render_day_card(request: Request, db: Session, target: date) -> HTMLResponse:
    ctx = day_card_context(db, target)
    ctx["request"] = request
    html = templates.get_template("partials/day_card.html").render(ctx)
    return HTMLResponse(html)


@router.post("/exercise/{log_id}/toggle")
def toggle_log(
    log_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_user),
    _: None = Depends(verify_csrf),
):
    log = db.get(ExerciseLog, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Exercise log not found")
    day = log.workout_day
    workout.toggle_log(db, day, log)
    return _render_day_card(request, db, date.fromisoformat(day.date))


@router.post("/skip")
async def skip_day(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_user),
    _: None = Depends(verify_csrf),
):
    form = await request.form()
    date_str = form.get("date") or schedule.today_in_tz(get_tz(db)).isoformat()
    reason = (form.get("reason") or "").strip() or None
    target = date.fromisoformat(date_str)
    program = plan_loader.load_program()
    day, _, _ = workout.get_or_create_workout_day(db, target, program, get_start_date(db))
    workout.skip_day(db, day, reason)
    return _render_day_card(request, db, target)


def _int_or_none(value: str | None) -> int | None:
    if value is None or not str(value).strip():
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def _float_or_none(value: str | None) -> float | None:
    if value is None or not str(value).strip():
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _parse_reps_input(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    parts = [p.strip() for p in value.replace(",", " ").split() if p.strip()]
    nums = [int(p) for p in parts if p.lstrip("-").isdigit()]
    if not nums:
        return None
    return json.dumps(nums)


def _parse_duration_input(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    value = value.strip()
    if ":" in value:
        try:
            m, s = value.split(":", 1)
            return int(m) * 60 + int(s)
        except ValueError:
            return None
    return _int_or_none(value)


@router.post("/exercise/{log_id}/update")
async def update_log_details(
    log_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_user),
    _: None = Depends(verify_csrf),
):
    log = db.get(ExerciseLog, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Exercise log not found")

    form = await request.form()
    rpe = _int_or_none(form.get("rpe"))
    data = {
        "actual_sets": _int_or_none(form.get("actual_sets")),
        "actual_reps": _parse_reps_input(form.get("actual_reps")),
        "actual_duration_seconds": _parse_duration_input(form.get("actual_duration")),
        "actual_distance_meters": (
            _float_or_none(form.get("actual_distance")) * 1000
            if _float_or_none(form.get("actual_distance")) is not None
            else None
        ),
        "rpe": rpe if rpe is not None and 1 <= rpe <= 10 else None,
        "note": (form.get("note") or "").strip() or None,
    }
    workout.update_log_details(db, log, data)
    day = log.workout_day
    return _render_day_card(request, db, date.fromisoformat(day.date))
