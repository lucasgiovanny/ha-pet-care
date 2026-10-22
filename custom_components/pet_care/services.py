"""Services that write to a pet's record."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    AMOUNTS,
    DOMAIN,
    SERVICE_ADD_TREATMENT,
    SERVICE_DELETE_ENTRY,
    SERVICE_END_TREATMENT,
    SERVICE_EXPORT,
    SERVICE_LOG_CARE,
    SERVICE_LOG_DOSE,
    SERVICE_LOG_MEAL,
    SERVICE_LOG_SNACK,
    SERVICE_LOG_SYMPTOM,
    SERVICE_LOG_WEIGHT,
    SERVICE_SET_DUE,
    SERVICE_UPDATE_TREATMENT,
    SYMPTOMS,
    TREATMENT_KINDS,
)

if TYPE_CHECKING:
    from .tracker import PetTracker

PET = vol.Optional("config_entry_id")
NOTE = vol.Optional("note")
AT = vol.Optional("at")


def _opt(validator: Any) -> Any:
    """Scripts pass empty fields as None or ''; both mean 'not given'."""
    return vol.Any(None, vol.All(vol.Equal(""), lambda _: None), validator)


def _tracker(hass: HomeAssistant, call: ServiceCall) -> PetTracker:
    entries = [
        e for e in hass.config_entries.async_entries(DOMAIN) if e.state is ConfigEntryState.LOADED
    ]
    wanted = call.data.get("config_entry_id")
    if wanted:
        entries = [e for e in entries if e.entry_id == wanted]
    if len(entries) != 1:
        raise ServiceValidationError(
            "Choose the pet (config_entry_id)" if entries else "Pet not found"
        )
    return entries[0].runtime_data


def _times(value: Any) -> list[str]:
    items = value if isinstance(value, list) else str(value).replace(";", ",").split(",")
    return [str(cv.time(str(item).strip()))[:5] for item in items if str(item).strip()]


def async_setup_services(hass: HomeAssistant) -> None:
    async def log_care(call: ServiceCall) -> None:
        await _tracker(hass, call).async_log_care(
            call.data["care"], call.data.get("at"), call.data.get("note"), call.context
        )

    async def log_meal(call: ServiceCall) -> None:
        await _tracker(hass, call).async_log_meal(
            call.data.get("meal"),
            call.data["amount"],
            call.data.get("grams"),
            call.data.get("note"),
            call.data.get("at"),
            call.context,
        )

    async def log_snack(call: ServiceCall) -> None:
        await _tracker(hass, call).async_log_snack(
            call.data["what"],
            call.data.get("grams"),
            call.data.get("note"),
            call.data.get("at"),
            call.context,
        )

    async def log_symptom(call: ServiceCall) -> None:
        await _tracker(hass, call).async_log_symptom(
            call.data["symptom"], call.data.get("note"), call.data.get("at"), call.context
        )

    async def log_weight(call: ServiceCall) -> None:
        await _tracker(hass, call).async_log_weight(
            call.data["kg"], call.data.get("note"), call.data.get("at"), call.context
        )

    async def log_dose(call: ServiceCall) -> None:
        await _tracker(hass, call).async_log_dose(
            call.data["treatment"],
            call.data.get("status", "given"),
            call.data.get("time"),
            call.context,
        )

    async def add_treatment(call: ServiceCall) -> ServiceResponse:
        data = {**call.data, "times": _times(call.data["times"])}
        treatment = await _tracker(hass, call).async_add_treatment(data, call.context)
        return {"id": treatment["id"]}

    async def update_treatment(call: ServiceCall) -> None:
        data = dict(call.data)
        if "times" in data:
            data["times"] = _times(data["times"])
        await _tracker(hass, call).async_update_treatment(call.data["treatment"], data)

    async def end_treatment(call: ServiceCall) -> None:
        await _tracker(hass, call).async_end_treatment(call.data["treatment"], call.context)

    async def set_due(call: ServiceCall) -> None:
        await _tracker(hass, call).async_set_due(call.data["care"], call.data["date"])

    async def delete_entry(call: ServiceCall) -> None:
        await _tracker(hass, call).async_delete(call.data["entry"])

    async def export(call: ServiceCall) -> ServiceResponse:
        return await _tracker(hass, call).async_export()

    reg = hass.services.async_register
    reg(
        DOMAIN,
        SERVICE_LOG_CARE,
        log_care,
        vol.Schema(
            {
                PET: cv.string,
                vol.Required("care"): cv.string,
                AT: _opt(cv.datetime),
                NOTE: _opt(cv.string),
            }
        ),
    )
    reg(
        DOMAIN,
        SERVICE_LOG_MEAL,
        log_meal,
        vol.Schema(
            {
                PET: cv.string,
                vol.Optional("meal"): _opt(cv.string),
                vol.Required("amount"): vol.In(AMOUNTS),
                vol.Optional("grams"): _opt(vol.Coerce(float)),
                AT: _opt(cv.datetime),
                NOTE: _opt(cv.string),
            }
        ),
    )
    reg(
        DOMAIN,
        SERVICE_LOG_SNACK,
        log_snack,
        vol.Schema(
            {
                PET: cv.string,
                vol.Required("what"): cv.string,
                vol.Optional("grams"): _opt(vol.Coerce(float)),
                AT: _opt(cv.datetime),
                NOTE: _opt(cv.string),
            }
        ),
    )
    reg(
        DOMAIN,
        SERVICE_LOG_SYMPTOM,
        log_symptom,
        vol.Schema(
            {
                PET: cv.string,
                vol.Required("symptom"): vol.In(SYMPTOMS),
                AT: _opt(cv.datetime),
                NOTE: _opt(cv.string),
            }
        ),
    )
    reg(
        DOMAIN,
        SERVICE_LOG_WEIGHT,
        log_weight,
        vol.Schema(
            {
                PET: cv.string,
                vol.Required("kg"): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=150)),
                AT: _opt(cv.datetime),
                NOTE: _opt(cv.string),
            }
        ),
    )
    reg(
        DOMAIN,
        SERVICE_LOG_DOSE,
        log_dose,
        vol.Schema(
            {
                PET: cv.string,
                vol.Required("treatment"): cv.string,
                vol.Optional("status", default="given"): vol.In(["given", "skipped"]),
                vol.Optional("time"): _opt(cv.string),
            }
        ),
    )
    treatment_fields: dict[Any, Any] = {
        vol.Optional("kind"): _opt(vol.In(TREATMENT_KINDS)),
        vol.Optional("dose"): _opt(cv.string),
        vol.Optional("start"): _opt(cv.date),
        vol.Optional("end"): _opt(cv.date),
        NOTE: _opt(cv.string),
    }
    reg(
        DOMAIN,
        SERVICE_ADD_TREATMENT,
        add_treatment,
        vol.Schema(
            {
                PET: cv.string,
                vol.Required("name"): cv.string,
                vol.Required("times"): vol.Any(cv.string, [cv.string]),
                **treatment_fields,
            }
        ),
        supports_response=SupportsResponse.OPTIONAL,
    )
    reg(
        DOMAIN,
        SERVICE_UPDATE_TREATMENT,
        update_treatment,
        vol.Schema(
            {
                PET: cv.string,
                vol.Required("treatment"): cv.string,
                vol.Optional("name"): cv.string,
                vol.Optional("times"): vol.Any(cv.string, [cv.string]),
                **treatment_fields,
            }
        ),
    )
    reg(
        DOMAIN,
        SERVICE_END_TREATMENT,
        end_treatment,
        vol.Schema({PET: cv.string, vol.Required("treatment"): cv.string}),
    )
    reg(
        DOMAIN,
        SERVICE_SET_DUE,
        set_due,
        vol.Schema(
            {PET: cv.string, vol.Required("care"): cv.string, vol.Required("date"): cv.date}
        ),
    )
    reg(
        DOMAIN,
        SERVICE_DELETE_ENTRY,
        delete_entry,
        vol.Schema({PET: cv.string, vol.Required("entry"): cv.string}),
    )
    reg(
        DOMAIN,
        SERVICE_EXPORT,
        export,
        vol.Schema({PET: cv.string}),
        supports_response=SupportsResponse.OPTIONAL,
    )
