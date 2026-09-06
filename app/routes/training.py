"""Training actions: check activities, mark a day missed, add/remove own activities."""
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


@router.post("/missed")
async def mark_missed(
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
    workout.mark_missed(db, day, reason)
    return _render_day_card(request, db, target)


@router.post("/exercise/add")
async def add_custom(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_user),
    _: None = Depends(verify_csrf),
):
    form = await request.form()
    date_str = form.get("date") or schedule.today_in_tz(get_tz(db)).isoformat()
    name = (form.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Activity name is required")
    target = date.fromisoformat(date_str)
    program = plan_loader.load_program()
    day, _, _ = workout.get_or_create_workout_day(db, target, program, get_start_date(db))
    workout.add_custom_log(db, day, name)
    return _render_day_card(request, db, target)


@router.post("/exercise/{log_id}/delete")
def delete_custom(
    log_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_user),
    _: None = Depends(verify_csrf),
):
    log = db.get(ExerciseLog, log_id)
    if log is None:
        raise HTTPException(status_code=404, detail="Exercise log not found")
    if log.exercise_key != workout.CUSTOM_KEY:
        raise HTTPException(status_code=400, detail="Only own activities can be removed")
    day = log.workout_day
    workout.delete_log(db, day, log)
    return _render_day_card(request, db, date.fromisoformat(day.date))
