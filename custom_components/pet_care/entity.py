"""Base entity: a thin view over the pet's tracker."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, signal_updated
from .tracker import PetTracker


class PetEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, tracker: PetTracker, key: str) -> None:
        self.tracker = tracker
        self._attr_unique_id = f"{tracker.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, tracker.entry_id)},
            name=tracker.pet,
            manufacturer="Pet Care",
            model=tracker.options.get("species", "dog"),
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, signal_updated(self.tracker.entry_id), self.async_write_ha_state
            )
        )
