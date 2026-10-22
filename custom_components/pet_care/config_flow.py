"""Add a pet, then shape its meals and care from the options."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.util import slugify

from .const import (
    CARE_INTERVAL,
    CARE_KINDS,
    CARE_SHEDDING,
    CARE_SUNNY,
    CONF_BATH_TIMES,
    CONF_CARE,
    CONF_FOOD,
    CONF_FOOD_GRAMS,
    CONF_MEALS,
    CONF_PET_NAME,
    CONF_PLAN_WEEKDAY,
    CONF_REMINDER_TIME,
    CONF_SPECIES,
    CONF_WEATHER,
    CONF_WEIGHT_DAY,
    DEFAULT_BATH_TIMES,
    DEFAULT_MEALS,
    DEFAULT_PLAN_WEEKDAY,
    DEFAULT_REMINDER_TIME,
    DEFAULT_WEIGHT_DAY,
    DOMAIN,
    SPECIES,
)


def default_care(language: str | None, species: str) -> list[dict[str, Any]]:
    """A starting set for a dog or cat; every item can be edited or removed afterwards."""
    pt = (language or "").startswith("pt")
    care = [
        {
            "key": "bath",
            "name": "Banho" if pt else "Bath",
            "kind": CARE_SUNNY,
            "interval_days": 7,
            "lead_days": 0,
            "icon": "mdi:shower-head",
        },
        {
            "key": "brushing",
            "name": "Escovação" if pt else "Brushing",
            "kind": CARE_SHEDDING,
            "interval_days": 7,
            "shedding_interval_days": 2,
            "lead_days": 0,
            "icon": "mdi:brush",
        },
        {
            "key": "deworming",
            "name": "Desparasitação interna" if pt else "Internal deworming",
            "kind": CARE_INTERVAL,
            "interval_days": 84,
            "lead_days": 1,
            "icon": "mdi:pill",
        },
        {
            "key": "flea",
            "name": "Desparasitação externa" if pt else "External parasite protection",
            "kind": CARE_INTERVAL,
            "interval_days": 182,
            "lead_days": 7,
            "icon": "mdi:shield-bug",
        },
    ]
    return care if species == "dog" else [c for c in care if c["key"] != "bath"]


def default_meals(language: str | None) -> list[dict[str, Any]]:
    if (language or "").startswith("pt"):
        return DEFAULT_MEALS
    return [
        {"key": "morning", "name": "Morning", "time": "07:45"},
        {"key": "evening", "name": "Evening", "time": "19:45"},
    ]


class PetCareConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            name = user_input[CONF_PET_NAME].strip()
            await self.async_set_unique_id(slugify(name))
            self._abort_if_unique_id_configured()
            language = self.hass.config.language
            options = {
                "sex": user_input.get("sex", "female"),
                CONF_WEATHER: user_input.get(CONF_WEATHER),
                CONF_MEALS: default_meals(language),
                CONF_CARE: default_care(language, user_input[CONF_SPECIES]),
                CONF_REMINDER_TIME: DEFAULT_REMINDER_TIME,
                CONF_BATH_TIMES: DEFAULT_BATH_TIMES,
                CONF_PLAN_WEEKDAY: DEFAULT_PLAN_WEEKDAY,
                CONF_WEIGHT_DAY: DEFAULT_WEIGHT_DAY,
            }
            return self.async_create_entry(
                title=name,
                data={CONF_PET_NAME: name, CONF_SPECIES: user_input[CONF_SPECIES]},
                options=options,
            )
        schema = vol.Schema(
            {
                vol.Required(CONF_PET_NAME): str,
                vol.Required(CONF_SPECIES, default="dog"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=SPECIES, translation_key="species")
                ),
                vol.Required("sex", default="female"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=["female", "male"], translation_key="sex")
                ),
                vol.Optional(CONF_WEATHER): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="weather")
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return PetCareOptionsFlow()


class PetCareOptionsFlow(OptionsFlow):
    def __init__(self) -> None:
        self._editing: str | None = None

    @property
    def _opts(self) -> dict[str, Any]:
        return dict(self.config_entry.options)

    def _save(self, **changes: Any) -> ConfigFlowResult:
        return self.async_create_entry(data={**self._opts, **changes})

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=["general", "meals", "care_add", "care_edit", "care_remove"],
        )

    async def async_step_general(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        opts = self._opts
        if user_input is not None:
            user_input[CONF_BATH_TIMES] = [
                t.strip()[:5] for t in user_input[CONF_BATH_TIMES].split(",") if t.strip()
            ]
            user_input[CONF_PLAN_WEEKDAY] = int(user_input[CONF_PLAN_WEEKDAY])
            user_input[CONF_WEIGHT_DAY] = int(user_input[CONF_WEIGHT_DAY])
            user_input[CONF_REMINDER_TIME] = str(user_input[CONF_REMINDER_TIME])[:5]
            return self._save(**user_input)
        schema = vol.Schema(
            {
                vol.Required("sex", default=opts.get("sex", "female")): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=["female", "male"], translation_key="sex")
                ),
                vol.Optional(
                    CONF_WEATHER, description={"suggested_value": opts.get(CONF_WEATHER)}
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="weather")),
                vol.Optional(CONF_FOOD, description={"suggested_value": opts.get(CONF_FOOD)}): str,
                vol.Optional(
                    CONF_FOOD_GRAMS, description={"suggested_value": opts.get(CONF_FOOD_GRAMS)}
                ): vol.Coerce(float),
                vol.Required(
                    CONF_REMINDER_TIME, default=opts.get(CONF_REMINDER_TIME, DEFAULT_REMINDER_TIME)
                ): selector.TimeSelector(),
                vol.Required(
                    CONF_BATH_TIMES,
                    default=", ".join(opts.get(CONF_BATH_TIMES, DEFAULT_BATH_TIMES)),
                ): str,
                vol.Required(
                    CONF_PLAN_WEEKDAY,
                    default=str(opts.get(CONF_PLAN_WEEKDAY, DEFAULT_PLAN_WEEKDAY)),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[str(i) for i in range(7)], translation_key="weekday"
                    )
                ),
                vol.Required(
                    CONF_WEIGHT_DAY, default=opts.get(CONF_WEIGHT_DAY, DEFAULT_WEIGHT_DAY)
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1, max=28, mode=selector.NumberSelectorMode.BOX
                    )
                ),
            }
        )
        return self.async_show_form(step_id="general", data_schema=schema)

    async def async_step_meals(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        meals = self._opts.get(CONF_MEALS) or DEFAULT_MEALS
        if user_input is not None:
            parsed: list[dict[str, Any]] = []
            for line in user_input["meals"].replace(";", ",").split(","):
                if "=" not in line:
                    continue
                name, at = (part.strip() for part in line.split("=", 1))
                parsed.append(
                    {"key": slugify(name) or f"meal{len(parsed)}", "name": name, "time": at[:5]}
                )
            if not parsed:
                return self.async_show_form(
                    step_id="meals",
                    data_schema=self._meals_schema(user_input["meals"]),
                    errors={"meals": "no_meals"},
                )
            return self._save(**{CONF_MEALS: parsed})
        return self.async_show_form(
            step_id="meals",
            data_schema=self._meals_schema(", ".join(f"{m['name']}={m['time']}" for m in meals)),
        )

    @staticmethod
    def _meals_schema(default: str) -> vol.Schema:
        return vol.Schema({vol.Required("meals", default=default): str})

    def _care_schema(self, care: dict[str, Any] | None = None) -> vol.Schema:
        care = care or {}
        return vol.Schema(
            {
                vol.Required("name", default=care.get("name", "")): str,
                vol.Required(
                    "kind", default=care.get("kind", CARE_INTERVAL)
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=CARE_KINDS, translation_key="care_kind")
                ),
                vol.Required(
                    "interval_days", default=care.get("interval_days", 30)
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1, max=730, mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Optional(
                    "shedding_interval_days",
                    description={"suggested_value": care.get("shedding_interval_days")},
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1, max=365, mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Required(
                    "lead_days", default=care.get("lead_days", 0)
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=60, mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Optional(
                    "icon", description={"suggested_value": care.get("icon")}
                ): selector.IconSelector(),
            }
        )

    @staticmethod
    def _clean(user_input: dict[str, Any]) -> dict[str, Any]:
        care = {k: v for k, v in user_input.items() if v not in (None, "")}
        for key in ("interval_days", "shedding_interval_days", "lead_days"):
            if key in care:
                care[key] = int(care[key])
        return care

    async def async_step_care_add(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            care = self._clean(user_input)
            existing = {c["key"] for c in self._opts.get(CONF_CARE, [])}
            key = slugify(care["name"]) or "care"
            while key in existing:
                key += "_2"
            return self._save(**{CONF_CARE: [*self._opts.get(CONF_CARE, []), {"key": key, **care}]})
        return self.async_show_form(step_id="care_add", data_schema=self._care_schema())

    def _care_picker(self) -> vol.Schema:
        options = [
            selector.SelectOptionDict(value=c["key"], label=c["name"])
            for c in self._opts.get(CONF_CARE, [])
        ]
        return vol.Schema(
            {
                vol.Required("care"): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=options)
                )
            }
        )

    async def async_step_care_edit(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._editing = user_input["care"]
            return await self.async_step_care_edit_form()
        return self.async_show_form(step_id="care_edit", data_schema=self._care_picker())

    async def async_step_care_edit_form(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        care_list = self._opts.get(CONF_CARE, [])
        current = next(c for c in care_list if c["key"] == self._editing)
        if user_input is not None:
            updated = {"key": current["key"], **self._clean(user_input)}
            return self._save(
                **{CONF_CARE: [updated if c["key"] == current["key"] else c for c in care_list]}
            )
        return self.async_show_form(
            step_id="care_edit_form",
            data_schema=self._care_schema(current),
            description_placeholders={"care": current["name"]},
        )

    async def async_step_care_remove(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self._save(
                **{
                    CONF_CARE: [
                        c for c in self._opts.get(CONF_CARE, []) if c["key"] != user_input["care"]
                    ]
                }
            )
        return self.async_show_form(step_id="care_remove", data_schema=self._care_picker())
