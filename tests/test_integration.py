"""Setup, services and reminders end to end."""

from datetime import timedelta

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_capture_events,
    async_fire_time_changed,
)

from custom_components.pet_care.config_flow import default_care, default_meals
from custom_components.pet_care.const import DOMAIN, EVENT_REMINDER, EVENT_RESOLVED


@pytest.fixture
async def pet(hass: HomeAssistant) -> MockConfigEntry:
    hass.config.language = "pt"
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Alaska",
        data={"pet_name": "Alaska", "species": "dog"},
        options={"sex": "female", "meals": default_meals("pt"), "care": default_care("pt", "dog")},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_config_flow_creates_a_pet(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"pet_name": "Rex", "species": "dog", "sex": "male"}
    )
    assert result["type"] == "create_entry"
    assert [c["key"] for c in result["options"]["care"]] == [
        "bath",
        "brushing",
        "deworming",
        "flea",
    ]


async def test_entities_and_meal(hass: HomeAssistant, pet: MockConfigEntry) -> None:
    states = {
        s.entity_id
        for s in hass.states.async_all()
        if s.entity_id.split(".")[1].startswith("alaska")
    }
    assert "sensor.alaska_peso" in states
    assert hass.states.get("sensor.alaska_refeicao_manha").state == "pending"
    resolved = async_capture_events(hass, EVENT_RESOLVED)
    await hass.services.async_call(
        DOMAIN, "log_meal", {"meal": "morning", "amount": "half", "grams": 120}, blocking=True
    )
    await hass.async_block_till_done()
    morning = hass.states.get("sensor.alaska_refeicao_manha")
    assert morning.state == "half"
    assert morning.attributes["grams"] == 120
    assert resolved and resolved[0].data["tag"].endswith("meal-morning")


async def test_care_due_and_delete(hass: HomeAssistant, pet: MockConfigEntry) -> None:
    await hass.services.async_call(
        DOMAIN, "set_due", {"care": "deworming", "date": "2026-10-27"}, blocking=True
    )
    await hass.async_block_till_done()
    assert hass.states.get("sensor.alaska_desparasitacao_interna").state == "2026-10-27"
    await hass.services.async_call(
        DOMAIN, "log_care", {"care": "Desparasitação interna"}, blocking=True
    )
    await hass.async_block_till_done()
    expected = (dt_util.now().date() + timedelta(days=84)).isoformat()
    assert hass.states.get("sensor.alaska_desparasitacao_interna").state == expected
    tracker = pet.runtime_data
    entry_id = tracker.entries("care")[-1]["id"]
    await hass.services.async_call(DOMAIN, "delete_entry", {"entry": entry_id}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.alaska_desparasitacao_interna").state == "unknown"


async def test_treatment_reminder_and_dose(hass: HomeAssistant, pet: MockConfigEntry) -> None:
    now = dt_util.now().replace(second=0, microsecond=0) + timedelta(minutes=2)
    response = await hass.services.async_call(
        DOMAIN,
        "add_treatment",
        {"name": "Pomada", "kind": "ointment", "times": now.strftime("%H:%M")},
        blocking=True,
        return_response=True,
    )
    assert response["id"]
    reminders = async_capture_events(hass, EVENT_REMINDER)
    async_fire_time_changed(hass, now)
    await hass.async_block_till_done()
    doses = [r for r in reminders if r.data["kind"] == "dose"]
    assert doses and "Pomada" in doses[0].data["message"]
    action = doses[0].data["actions"][0]["action"]
    hass.bus.async_fire("mobile_app_notification_action", {"action": action})
    await hass.async_block_till_done()
    assert pet.runtime_data.dose_status(response["id"], now.strftime("%H:%M")) == "given"
    assert hass.states.get("sensor.alaska_tratamentos").state == "1"


async def test_symptom_weight_report_export(
    hass: HomeAssistant, pet: MockConfigEntry, tmp_path
) -> None:
    hass.config.media_dirs = {"local": str(tmp_path)}
    await hass.services.async_call(
        DOMAIN, "log_symptom", {"symptom": "vomit", "note": "de manhã"}, blocking=True
    )
    await hass.services.async_call(DOMAIN, "log_weight", {"kg": 31.4}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.alaska_peso").state == "31.4"
    assert hass.states.get("sensor.alaska_sintomas_em_30_dias").state == "1"
    result = await hass.services.async_call(
        DOMAIN, "export", {}, blocking=True, return_response=True
    )
    assert result["rows"] == 2
    assert (tmp_path / "pet_care").exists()


async def test_shedding_switch(hass: HomeAssistant, pet: MockConfigEntry) -> None:
    await hass.services.async_call(DOMAIN, "log_care", {"care": "brushing"}, blocking=True)
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.alaska_epoca_de_troca_de_pelo"}, blocking=True
    )
    await hass.async_block_till_done()
    assert hass.states.get("sensor.alaska_escovacao").attributes["interval_days"] == 2


async def test_bath_plan_uses_the_forecast(hass: HomeAssistant, pet: MockConfigEntry) -> None:
    from homeassistant.core import ServiceCall, SupportsResponse

    today = dt_util.now().date()
    forecasts = [
        {
            "datetime": (today + timedelta(days=d)).isoformat() + "T12:00:00+00:00",
            "condition": c,
            "temperature": t,
        }
        for d, c, t in ((0, "rainy", 18), (1, "sunny", 24), (2, "cloudy", 20))
    ]

    async def get_forecasts(call: ServiceCall):
        return {"weather.casa": {"forecast": forecasts}}

    hass.states.async_set("weather.casa", "sunny")
    hass.services.async_register(
        "weather", "get_forecasts", get_forecasts, supports_response=SupportsResponse.ONLY
    )
    hass.config_entries.async_update_entry(
        pet, options={**pet.options, "weather_entity": "weather.casa"}
    )
    await hass.async_block_till_done()
    await hass.services.async_call(
        DOMAIN,
        "set_due",
        {"care": "bath", "date": (today + timedelta(days=2)).isoformat()},
        blocking=True,
    )
    reminders = async_capture_events(hass, EVENT_REMINDER)
    await hass.services.async_call(
        "button", "press", {"entity_id": "button.alaska_escolher_dia_do_banho"}, blocking=True
    )
    await hass.async_block_till_done()
    assert hass.states.get("sensor.alaska_banho").state == (today + timedelta(days=1)).isoformat()
    assert reminders and "24 °C" in reminders[-1].data["message"]


async def test_daily_reminder_for_a_due_care(hass: HomeAssistant, pet: MockConfigEntry) -> None:
    today = dt_util.now().date()
    await hass.services.async_call(
        DOMAIN,
        "set_due",
        {"care": "flea", "date": (today + timedelta(days=7)).isoformat()},
        blocking=True,
    )
    reminders = async_capture_events(hass, EVENT_REMINDER)
    nine = dt_util.now().replace(hour=9, minute=0, second=0, microsecond=0)
    if nine < dt_util.now():
        nine += timedelta(days=1)
        await hass.services.async_call(
            DOMAIN,
            "set_due",
            {"care": "flea", "date": (today + timedelta(days=8)).isoformat()},
            blocking=True,
        )
    async_fire_time_changed(hass, nine)
    await hass.async_block_till_done()
    care = [r for r in reminders if r.data["kind"] == "care" and r.data["key"] == "flea"]
    assert care and "daqui a 7 dias" in care[0].data["message"]
