"""Authentication, CSRF protection, and login rate limiting.

Security model (single user):
- Argon2 password hashing.
- Starlette SessionMiddleware provides a signed, HttpOnly session cookie.
- A per-session CSRF token is verified on every unsafe request (header or form).
- A tiny in-memory rate limiter slows brute-force login attempts.
"""
from __future__ import annotations

import secrets
import time
from collections import defaultdict

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from app.database import get_db
from app.models import User

_hasher = PasswordHasher()

# --- Password helpers -------------------------------------------------------


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, Exception):
        return False


# --- CSRF -------------------------------------------------------------------


class EnsureCsrfTokenMiddleware(BaseHTTPMiddleware):
    """Make sure every session carries a CSRF token."""

    async def dispatch(self, request: Request, call_next):
        if "csrf_token" not in request.session:
            request.session["csrf_token"] = secrets.token_urlsafe(24)
        return await call_next(request)


async def verify_csrf(request: Request) -> None:
    """FastAPI dependency: reject unsafe requests without a valid CSRF token."""
    session_token = request.session.get("csrf_token")
    if not session_token:
        raise HTTPException(status_code=403, detail="CSRF token missing")

    token = request.headers.get("X-CSRF-Token")
    if not token:
        try:
            form = await request.form()
            token = form.get("csrf_token")
        except Exception:
            token = None

    if not token or not secrets.compare_digest(str(token), str(session_token)):
        raise HTTPException(status_code=403, detail="CSRF token mismatch")


# --- Authentication ---------------------------------------------------------


class LoginRequired(Exception):
    """Raised when an authenticated-only route is hit anonymously."""


def current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)


async def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    user = current_user(request, db)
    if user is None:
        raise LoginRequired()
    return user


# --- Login rate limiting ----------------------------------------------------

_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 300
_failures: dict[str, list[float]] = defaultdict(list)


def login_is_blocked(key: str) -> bool:
    now = time.time()
    attempts = [t for t in _failures[key] if now - t < _WINDOW_SECONDS]
    _failures[key] = attempts
    return len(attempts) >= _MAX_ATTEMPTS


def record_login_failure(key: str) -> None:
    _failures[key].append(time.time())


def login_delay_seconds() -> float:
    """A small constant delay to make brute force slower."""
    return 0.4
