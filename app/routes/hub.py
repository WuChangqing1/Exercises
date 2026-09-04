"""Product Hub routes (no authentication)."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.services.products import load_products
from app.templating import templates

router = APIRouter()


@router.get("/")
def hub(request: Request):
    products = load_products()
    return templates.TemplateResponse(
        request,
        "hub.html",
        {"products": products, "title": "Fengz Lab"},
    )


@router.get("/hub")
def hub_no_slash() -> RedirectResponse:
    return RedirectResponse("/", status_code=301)


@router.get("/hub/")
def hub_slash() -> RedirectResponse:
    return RedirectResponse("/", status_code=301)
