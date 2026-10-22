"""One button per care to record it as done now, and one to plan a sunny bath again."""

from __future__ import annotations

from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PetCareConfigEntry
from .const import CARE_SUNNY
from .entity import PetEntity
from .tracker import PetTracker


async def async_setup_entry(
    hass: HomeAssistant, entry: PetCareConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    tracker = entry.runtime_data
    entities: list[ButtonEntity] = [CareDoneButton(tracker, care) for care in tracker.care]
    if any(care.get("kind") == CARE_SUNNY for care in tracker.care):
        entities.append(PlanButton(tracker))
    async_add_entities(entities)


class CareDoneButton(PetEntity, ButtonEntity):
    _attr_translation_key = "care_done"

    def __init__(self, tracker: PetTracker, care: dict[str, Any]) -> None:
        super().__init__(tracker, f"done_{care['key']}")
        self.care = care
        self._attr_translation_placeholders = {"care": care["name"]}
        self._attr_icon = care.get("icon") or "mdi:check"

    async def async_press(self) -> None:
        await self.tracker.async_log_care(self.care["key"], context=self._context)


class PlanButton(PetEntity, ButtonEntity):
    _attr_translation_key = "plan_bath"
    _attr_icon = "mdi:weather-sunny"

    def __init__(self, tracker: PetTracker) -> None:
        super().__init__(tracker, "plan_bath")

    async def async_press(self) -> None:
        await self.tracker.async_plan_baths()
