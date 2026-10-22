"""Upcoming care dates as an all-day calendar."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import PetCareConfigEntry
from .entity import PetEntity
from .tracker import PetTracker


async def async_setup_entry(
    hass: HomeAssistant, entry: PetCareConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([PetCalendar(entry.runtime_data)])


class PetCalendar(PetEntity, CalendarEntity):
    _attr_translation_key = "calendar"
    _attr_icon = "mdi:calendar-heart"

    def __init__(self, tracker: PetTracker) -> None:
        super().__init__(tracker, "calendar")

    def _events(self) -> list[CalendarEvent]:
        return [
            CalendarEvent(
                start=item["day"],
                end=item["day"] + timedelta(days=1),
                summary=item["summary"],
                uid=item["uid"],
            )
            for item in self.tracker.calendar_items()
        ]

    @property
    def event(self) -> CalendarEvent | None:
        today = dt_util.now().date()
        return next((e for e in self._events() if e.start >= today), None)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        start: date = dt_util.as_local(start_date).date()
        end: date = dt_util.as_local(end_date).date()
        return [e for e in self._events() if e.end > start and e.start < end]
