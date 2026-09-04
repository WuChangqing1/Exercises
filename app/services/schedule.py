"""Schedule engine: week calculation and per-day plan resolution."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

DEFAULT_TZ = "Asia/Shanghai"

_DAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def get_timezone(timezone_str: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_str or DEFAULT_TZ)
    except Exception:
        return ZoneInfo(DEFAULT_TZ)


def today_in_tz(timezone_str: str | None = None) -> date:
    return datetime.now(get_timezone(timezone_str)).date()


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def week_number(start: date, target: date, total_weeks: int) -> tuple[int, bool]:
    """Return (1-based week clamped to [1, total], whether program is finished)."""
    delta = (target - start).days
    if delta < 0:
        return 1, False
    week = delta // 7 + 1
    finished = week > total_weeks
    return max(1, min(week, total_weeks)), finished


def get_day_plan(program: dict[str, Any], target: date, week: int) -> dict[str, Any]:
    """Resolve the plan for a single calendar day, applying week overrides."""
    weekday = target.weekday()  # 0=Monday
    template = program.get("weekdays", {}).get(weekday, {})
    day_name = _DAY_NAMES[weekday]

    result: dict[str, Any] = {
        "type": template.get("type", ""),
        "rest": bool(template.get("rest", False)),
        "exercises": [],
    }

    overrides = program.get("week_overrides", {}).get(week, {}).get(day_name, {})

    for ex in template.get("exercises", []):
        item = dict(ex) if isinstance(ex, dict) else {}
        extra = overrides.get(item.get("key"), {}) if isinstance(overrides, dict) else {}
        if isinstance(extra, dict):
            item.update(extra)
        result["exercises"].append(item)

    return result
