"""Load the training plan YAML with a small in-memory cache."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import yaml

from app.config import settings


@lru_cache(maxsize=4)
def load_program(path: str | None = None) -> dict[str, Any]:
    path = path or settings.training_plan_path
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or "weekdays" not in data:
        raise ValueError(f"Invalid training plan: {path}")
    return data


def total_weeks(program: dict[str, Any]) -> int:
    return int(program.get("program", {}).get("weeks", 8))


def maintenance_week(program: dict[str, Any]) -> int:
    return int(program.get("program", {}).get("maintenance_week", total_weeks(program)))
