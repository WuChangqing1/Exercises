"""Product Hub registry loader.

The registry is a YAML file kept separate from code so products can change
without a code deploy. Loading failures degrade to a safe fallback that only
shows the Training Tracker, never an exception.
"""
from __future__ import annotations

import os
from typing import Any

import yaml

from app.config import settings

_FALLBACK_PRODUCTS: list[dict[str, Any]] = [
    {
        "id": "training",
        "name": "Training Tracker",
        "description": "Personal workout planning and training tracking.",
        "url": "/training/",
        "icon": "🏋️",
        "accent": "#6366f1",
        "accentRGB": "99, 102, 241",
        "tags": ["training"],
        "enabled": True,
        "order": 10,
    }
]


def load_products(path: str | None = None) -> list[dict[str, Any]]:
    """Return enabled products ordered by `order`, or a safe fallback."""
    path = path or settings.products_config_path
    if not path or not os.path.exists(path):
        return _FALLBACK_PRODUCTS

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except Exception:
        return _FALLBACK_PRODUCTS

    raw = data.get("products", []) if isinstance(data, dict) else []
    if not isinstance(raw, list):
        return _FALLBACK_PRODUCTS

    products: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        if not item.get("enabled", True):
            continue
        if not item.get("url") or not item.get("name"):
            continue
        products.append(item)

    products.sort(key=lambda p: (int(p.get("order", 0) or 0), str(p.get("id", ""))))
    return products or _FALLBACK_PRODUCTS
