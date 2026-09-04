"""Exercises Platform FastAPI application."""
from __future__ import annotations

from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.routes import (
    auth,
    calendar,
    dashboard,
    health,
    hub,
    pwa,
    settings as settings_routes,
    stats,
    training,
)
from app.security import EnsureCsrfTokenMiddleware, LoginRequired

app = FastAPI(title="Exercises Platform", version="0.1.0")

# Order matters: SessionMiddleware must be outermost so EnsureCsrfTokenMiddleware
# can read the populated request.session.
app.add_middleware(EnsureCsrfTokenMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.effective_secret_key(),
    https_only=settings.session_secure,
    same_site="lax",
    max_age=14 * 24 * 3600,
)


@app.exception_handler(LoginRequired)
async def login_required_handler(request: Request, exc: LoginRequired):
    next_url = request.url.path
    if request.url.query:
        next_url += f"?{request.url.query}"
    return RedirectResponse(f"/training/login?next={quote(next_url)}", status_code=303)


app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/training/static", StaticFiles(directory="app/training_static"), name="training_static")

app.include_router(hub.router)
app.include_router(health.router)
app.include_router(pwa.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(training.router)
app.include_router(calendar.router)
app.include_router(stats.router)
app.include_router(settings_routes.router)
