"""Jinja2 template engine and custom filters."""
from __future__ import annotations

import json

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

_WEEKDAYS_CN = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]


def cn_date(value) -> str:
    """Format a date as e.g. '9月7日 星期一'."""
    if value is None:
        return ""
    return f"{value.month}月{value.day}日 {_WEEKDAYS_CN[value.weekday()]}"


def weekday_cn(value) -> str:
    if value is None:
        return ""
    return _WEEKDAYS_CN[value.weekday()]


def reps_display(value) -> str:
    """Render a JSON reps list like '[5,5,4,3]' as '5 5 4 3'."""
    if not value:
        return ""
    try:
        data = json.loads(value)
        if isinstance(data, list):
            return " ".join(str(x) for x in data)
    except Exception:
        pass
    return str(value)


def seconds_display(value) -> str:
    if value is None:
        return ""
    m, s = divmod(int(value), 60)
    if m:
        return f"{m}:{s:02d}"
    return str(s)


templates.env.filters["cn_date"] = cn_date
templates.env.filters["weekday_cn"] = weekday_cn
templates.env.filters["reps_display"] = reps_display
templates.env.filters["seconds_display"] = seconds_display
