"""A late flag for each care."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PetCareConfigEntry
from .entity import PetEntity
from .tracker import PetTracker


async def async_setup_entry(
    hass: HomeAssistant, entry: PetCareConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(CareLate(entry.runtime_data, care) for care in entry.runtime_data.care)


class CareLate(PetEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "late"

    def __init__(self, tracker: PetTracker, care: dict[str, Any]) -> None:
        super().__init__(tracker, f"late_{care['key']}")
        self.care = care
        self._attr_translation_placeholders = {"care": care["name"]}

    @property
    def is_on(self) -> bool:
        return self.tracker.care_state(self.care)["overdue"]
