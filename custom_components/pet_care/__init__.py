"""Pet Care: meals, care with due dates, treatments, symptoms and weight for each pet."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .const import DOMAIN
from .services import async_setup_services
from .tracker import PetTracker

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CALENDAR,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type PetCareConfigEntry = ConfigEntry[PetTracker]


CARD_URL = f"/{DOMAIN}/pet-care-card.js"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async_setup_services(hass)
    # The card ships with the integration: no separate resource to install.
    version = (await async_get_integration(hass, DOMAIN)).version
    if "frontend" not in hass.config.components:
        return True
    from homeassistant.components.frontend import add_extra_js_url

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                CARD_URL, str(Path(__file__).parent / "frontend" / "pet-care-card.js"), False
            )
        ]
    )
    add_extra_js_url(hass, f"{CARD_URL}?v={version}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: PetCareConfigEntry) -> bool:
    tracker = PetTracker(hass, entry.entry_id, {**entry.data, **entry.options})
    await tracker.async_load()
    entry.runtime_data = tracker
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    tracker.async_start()
    entry.async_on_unload(tracker.async_stop)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PetCareConfigEntry) -> bool:
    await entry.runtime_data.async_flush()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: PetCareConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
