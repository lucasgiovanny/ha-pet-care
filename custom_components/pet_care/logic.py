"""Pure scheduling rules: when care is due, which day suits a bath, which doses a day holds."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from .const import CARE_SHEDDING, MORNING_UNTIL_HOUR, REPEAT_MINUTES

SUNNY = {"sunny": 3.0, "clear-night": 3.0, "partlycloudy": 2.0, "cloudy": 0.5, "windy": 0.5}
WET = {"rainy", "pouring", "lightning", "lightning-rainy", "snowy", "snowy-rainy", "hail"}


def parse_time(value: str) -> time:
    """'07:45' or '07:45:00' to a time."""
    parts = [int(p) for p in str(value).split(":")]
    return time(parts[0], parts[1] if len(parts) > 1 else 0)


def parse_date(value: str | date | None) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def care_interval(care: dict[str, Any], shedding: bool) -> int:
    """Days between two of this care; grooming shortens while the coat sheds."""
    if care.get("kind") == CARE_SHEDDING and shedding and care.get("shedding_interval_days"):
        return int(care["shedding_interval_days"])
    return int(care["interval_days"])


def care_next_due(care: dict[str, Any], shedding: bool) -> date | None:
    """A due date set by hand wins until the care is done after it; otherwise last + interval."""
    last = parse_date(care.get("last_done"))
    override = parse_date(care.get("next_due"))
    if override and (last is None or override > last):
        return override
    if last is None:
        return None
    return last + timedelta(days=care_interval(care, shedding))


def care_reminder(care: dict[str, Any], today: date, shedding: bool) -> str | None:
    """What the daily reminder says about this care today: lead, due, overdue or nothing."""
    due = care_next_due(care, shedding)
    if due is None:
        return None
    lead = int(care.get("lead_days") or 0)
    if today > due:
        return "overdue"
    if today == due:
        return "due"
    if lead and today == due - timedelta(days=lead):
        return "lead"
    return None


def day_score(forecast: dict[str, Any]) -> float:
    """How good a day looks for a bath that has to dry: sun, warmth, no rain."""
    condition = forecast.get("condition")
    if condition in WET:
        return -10.0
    score = SUNNY.get(str(condition), 0.0)
    temp = forecast.get("temperature")
    if temp is not None:
        score += float(temp) / 5
    rain = forecast.get("precipitation_probability")
    if rain is not None:
        score -= float(rain) / 25
    return score


def plan_bath(
    today: date, deadline: date, forecasts: list[dict[str, Any]]
) -> tuple[date, dict[str, Any] | None]:
    """The best-looking day from today up to the deadline; the deadline when nothing is known."""
    if deadline <= today:
        return today, _forecast_for(forecasts, today)
    best: tuple[float, date, dict[str, Any]] | None = None
    for forecast in forecasts:
        day = parse_date(forecast.get("datetime"))
        if day is None or day < today or day > deadline:
            continue
        score = day_score(forecast)
        if best is None or score > best[0]:
            best = (score, day, forecast)
    if best is None:
        return deadline, None
    return best[1], best[2]


def _forecast_for(forecasts: list[dict[str, Any]], day: date) -> dict[str, Any] | None:
    return next((f for f in forecasts if parse_date(f.get("datetime")) == day), None)


def meal_slot_for(moment: datetime, meals: list[dict[str, Any]]) -> str:
    """The meal a bare 'she ate' belongs to: the first before the afternoon, the last after."""
    if len(meals) == 1 or moment.hour < MORNING_UNTIL_HOUR:
        return meals[0]["key"]
    return meals[-1]["key"]


def day_of(moment: datetime, rollover_hour: int) -> date:
    """The care day a moment belongs to; the small hours still count as the day before."""
    if moment.hour < rollover_hour:
        return (moment - timedelta(days=1)).date()
    return moment.date()


def treatment_active_on(treatment: dict[str, Any], day: date) -> bool:
    if treatment.get("ended"):
        return False
    start = parse_date(treatment.get("start"))
    end = parse_date(treatment.get("end"))
    return (start is None or start <= day) and (end is None or day <= end)


def repeat_index(now: datetime, at: time) -> int | None:
    """0 at the scheduled minute, 1-3 at each repeat after it, None any other minute."""
    base = now.replace(hour=at.hour, minute=at.minute, second=0, microsecond=0)
    minutes = round((now.replace(second=0, microsecond=0) - base).total_seconds() / 60)
    if minutes == 0:
        return 0
    if minutes in REPEAT_MINUTES:
        return REPEAT_MINUTES.index(minutes) + 1
    return None
