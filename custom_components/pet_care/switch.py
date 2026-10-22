"""Shedding season: grooming comes round more often while it is on."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PetCareConfigEntry
from .const import CARE_SHEDDING
from .entity import PetEntity
from .tracker import PetTracker


async def async_setup_entry(
    hass: HomeAssistant, entry: PetCareConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    if any(care.get("kind") == CARE_SHEDDING for care in entry.runtime_data.care):
        async_add_entities([SheddingSwitch(entry.runtime_data)])


class SheddingSwitch(PetEntity, SwitchEntity):
    _attr_translation_key = "shedding"
    _attr_icon = "mdi:dog-side"

    def __init__(self, tracker: PetTracker) -> None:
        super().__init__(tracker, "shedding")

    @property
    def is_on(self) -> bool:
        return self.tracker.shedding

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.tracker.set_shedding(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.tracker.set_shedding(False)
