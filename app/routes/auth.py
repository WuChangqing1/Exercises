"""Authentication routes: login / logout."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import (
    current_user,
    login_delay_seconds,
    login_is_blocked,
    record_login_failure,
    verify_csrf,
    verify_password,
)
from app.templating import templates

router = APIRouter(prefix="/training", tags=["auth"])


@router.get("/login")
def login_page(request: Request, db: Session = Depends(get_db)):
    if current_user(request, db) is not None:
        return RedirectResponse("/training/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
async def login_submit(
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(verify_csrf),
):
    form = await request.form()
    username = (form.get("username") or "").strip()
    password = form.get("password") or ""

    key = f"{request.client.host if request.client else 'unknown'}:{username}"
    if login_is_blocked(key):
        raise HTTPException(status_code=429, detail="Too many attempts. Try again later.")

    user = db.scalar(select(User).where(User.username == username))
    if user is not None and verify_password(user.password_hash, password):
        request.session.clear()
        request.session["user_id"] = user.id
        return RedirectResponse("/training/", status_code=303)

    record_login_failure(key)
    time.sleep(login_delay_seconds())
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": "用户名或密码错误"},
        status_code=401,
    )


@router.post("/logout")
def logout(request: Request, _: None = Depends(verify_csrf)):
    request.session.clear()
    return RedirectResponse("/training/login", status_code=303)
