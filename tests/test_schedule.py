"""Schedule engine tests."""
from datetime import date

from app.services import plan_loader, schedule


def test_program_start_is_monday():
    assert date(2026, 9, 7).weekday() == 0


def test_week_number():
    start = date(2026, 9, 7)
    assert schedule.week_number(start, start, 8) == (1, False)
    assert schedule.week_number(start, date(2026, 9, 14), 8) == (2, False)
    assert schedule.week_number(start, date(2026, 11, 2), 8) == (8, True)
    assert schedule.week_number(start, date(2026, 11, 9), 8) == (8, True)


def test_monday_plan():
    program = plan_loader.load_program()
    plan = schedule.get_day_plan(program, date(2026, 9, 7), 1)
    assert plan["rest"] is False
    assert plan["type"] == "背部 + 核心"
    keys = [e["key"] for e in plan["exercises"]]
    assert "pullup" in keys
    assert "plank" in keys


def test_wednesday_is_rest():
    program = plan_loader.load_program()
    plan = schedule.get_day_plan(program, date(2026, 9, 9), 1)
    assert plan["rest"] is True


def test_week1_saturday_endurance():
    program = plan_loader.load_program()
    plan = schedule.get_day_plan(program, date(2026, 9, 12), 1)
    run = next(e for e in plan["exercises"] if e["key"] == "endurance_run")
    assert run["distance"] == "3 km"


def test_week8_saturday_endurance():
    program = plan_loader.load_program()
    plan = schedule.get_day_plan(program, date(2026, 10, 31), 8)
    run = next(e for e in plan["exercises"] if e["key"] == "endurance_run")
    assert run["distance"] == "6~7 km"
