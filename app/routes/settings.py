"""Settings, password change, export, and immediate backup."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.helpers import get_or_create_settings
from app.security import hash_password, require_user, verify_csrf, verify_password
from app.services import schedule
from app.services.backup import create_backup
from app.services.export import export_exercise_csv, export_json, export_workout_csv
from app.templating import templates

router = APIRouter(prefix="/training", tags=["settings"])


def _flash(request: Request, message: str) -> None:
    request.session["flash"] = message


def _pop_flash(request: Request) -> str | None:
    return request.session.pop("flash", None)


@router.get("/settings")
def settings_page(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    s = get_or_create_settings(db)
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "settings": s,
            "active_page": "settings",
            "message": _pop_flash(request),
            "error": None,
        },
    )


@router.post("/settings")
async def update_settings(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_user),
    _: None = Depends(verify_csrf),
):
    form = await request.form()
    s = get_or_create_settings(db)

    start_date = (form.get("program_start_date") or "").strip()
    timezone = (form.get("timezone") or "").strip()
    training_time = (form.get("default_training_time") or "").strip()

    error = None
    if start_date:
        try:
            date.fromisoformat(start_date)
        except ValueError:
            error = "开始日期格式无效，应为 YYYY-MM-DD"
    if timezone and not error:
        try:
            schedule.get_timezone(timezone)
        except Exception:
            error = "时区无效"
    if training_time and not error:
        parts = training_time.split(":")
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            error = "默认训练时间格式无效，应为 HH:MM"

    if error:
        return templates.TemplateResponse(
            request,
            "settings.html",
            {"settings": s, "active_page": "settings", "message": None, "error": error},
        )

    if start_date:
        s.program_start_date = start_date
    if timezone:
        s.timezone = timezone
    if training_time:
        s.default_training_time = training_time
    db.commit()

    _flash(request, "设置已保存")
    return RedirectResponse("/training/settings", status_code=303)


@router.post("/settings/password")
async def change_password(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_user),
    _: None = Depends(verify_csrf),
):
    form = await request.form()
    current = form.get("current_password") or ""
    new = form.get("new_password") or ""
    confirm = form.get("confirm_password") or ""

    error = None
    if not verify_password(user.password_hash, current):
        error = "当前密码错误"
    elif len(new) < 8:
        error = "新密码至少 8 位"
    elif new != confirm:
        error = "两次输入的新密码不一致"
    else:
        user.password_hash = hash_password(new)
        db.commit()
        _flash(request, "密码已修改")
        return RedirectResponse("/training/settings", status_code=303)

    s = get_or_create_settings(db)
    return templates.TemplateResponse(
        request,
        "settings.html",
        {"settings": s, "active_page": "settings", "message": None, "error": error},
    )


@router.get("/export")
def export_data(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_user),
    format: str = "json",
):
    if format == "csv_workout":
        content = "\ufeff" + export_workout_csv(db)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=workouts.csv"},
        )
    if format == "csv_exercise":
        content = "\ufeff" + export_exercise_csv(db)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=exercises.csv"},
        )
    return Response(
        content=export_json(db),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=exercises.json"},
    )


@router.post("/backup")
def backup_now(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_user),
    _: None = Depends(verify_csrf),
):
    path = create_backup()
    _flash(request, f"备份已创建")
    return RedirectResponse("/training/settings", status_code=303)
