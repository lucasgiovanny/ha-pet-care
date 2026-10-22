"""Scheduling rules."""

from datetime import date, datetime, time

from custom_components.pet_care.logic import (
    care_next_due,
    care_reminder,
    day_of,
    meal_slot_for,
    plan_bath,
    repeat_index,
    treatment_active_on,
)

DOG_BRUSH = {"key": "brushing", "kind": "shedding", "interval_days": 7, "shedding_interval_days": 2}


def test_next_due_from_last_and_override():
    care = {"interval_days": 84, "last_done": "2026-08-04"}
    assert care_next_due(care, False) == date(2026, 10, 27)
    assert care_next_due({**care, "next_due": "2026-10-30"}, False) == date(2026, 10, 30)
    # A due date older than the last time it was done no longer counts.
    assert care_next_due({**care, "next_due": "2026-08-01"}, False) == date(2026, 10, 27)
    assert care_next_due({"interval_days": 7}, False) is None


def test_shedding_shortens_grooming():
    care = {**DOG_BRUSH, "last_done": "2026-10-20"}
    assert care_next_due(care, False) == date(2026, 10, 27)
    assert care_next_due(care, True) == date(2026, 10, 22)


def test_reminder_lead_due_overdue():
    care = {"interval_days": 182, "lead_days": 7, "next_due": "2027-03-25"}
    assert care_reminder(care, date(2027, 3, 18), False) == "lead"
    assert care_reminder(care, date(2027, 3, 19), False) is None
    assert care_reminder(care, date(2027, 3, 25), False) == "due"
    assert care_reminder(care, date(2027, 3, 27), False) == "overdue"


def test_bath_picks_the_sunniest_day_before_the_deadline():
    forecasts = [
        {"datetime": "2026-10-26T12:00:00+00:00", "condition": "rainy", "temperature": 20},
        {"datetime": "2026-10-27T12:00:00+00:00", "condition": "cloudy", "temperature": 19},
        {"datetime": "2026-10-28T12:00:00+00:00", "condition": "sunny", "temperature": 22},
        {"datetime": "2026-10-29T12:00:00+00:00", "condition": "sunny", "temperature": 25},
        {"datetime": "2026-10-31T12:00:00+00:00", "condition": "sunny", "temperature": 30},
    ]
    day, forecast = plan_bath(date(2026, 10, 26), date(2026, 10, 29), forecasts)
    assert day == date(2026, 10, 29)
    assert forecast["temperature"] == 25


def test_bath_falls_back_to_the_deadline():
    assert plan_bath(date(2026, 10, 26), date(2026, 10, 29), [])[0] == date(2026, 10, 29)
    assert plan_bath(date(2026, 10, 26), date(2026, 10, 20), [])[0] == date(2026, 10, 26)


def test_meal_slot_and_care_day():
    meals = [{"key": "morning"}, {"key": "evening"}]
    assert meal_slot_for(datetime(2026, 10, 22, 9, 0), meals) == "morning"
    assert meal_slot_for(datetime(2026, 10, 22, 20, 0), meals) == "evening"
    assert day_of(datetime(2026, 10, 23, 2, 0), 4) == date(2026, 10, 22)


def test_repeats():
    at = time(19, 45)
    assert repeat_index(datetime(2026, 10, 22, 19, 45), at) == 0
    assert repeat_index(datetime(2026, 10, 22, 20, 0), at) == 1
    assert repeat_index(datetime(2026, 10, 22, 20, 30), at) == 3
    assert repeat_index(datetime(2026, 10, 22, 20, 31), at) is None


def test_treatment_window():
    treatment = {"start": "2026-10-22", "end": "2026-10-31"}
    assert treatment_active_on(treatment, date(2026, 10, 31))
    assert not treatment_active_on(treatment, date(2026, 11, 1))
    assert not treatment_active_on({**treatment, "ended": True}, date(2026, 10, 25))
