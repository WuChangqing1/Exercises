"""PWA manifest and service worker endpoints (scope /training/)."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["pwa"])


@router.get("/training/manifest.json")
def manifest():
    return FileResponse(
        "app/training_static/manifest.json",
        media_type="application/manifest+json",
    )


@router.get("/training/sw.js")
def service_worker():
    return FileResponse(
        "app/training_static/service-worker.js",
        media_type="application/javascript",
    )
