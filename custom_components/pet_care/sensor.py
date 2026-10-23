"""Sensors: each care's next date, today's meals, weight, treatments, the log and the report."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import PetCareConfigEntry
from .const import AMOUNTS, CARE_SUNNY, DOMAIN
from .entity import PetEntity
from .logic import parse_date, parse_time
from .tracker import PetTracker


async def async_setup_entry(
    hass: HomeAssistant, entry: PetCareConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    tracker = entry.runtime_data
    entities: list[SensorEntity] = [CareSensor(tracker, care) for care in tracker.care]
    entities += [MealSensor(tracker, meal) for meal in tracker.meals]
    entities += [
        WeightSensor(tracker),
        TreatmentsSensor(tracker),
        NextDoseSensor(tracker),
        LogSensor(tracker),
        ReportSensor(tracker),
        SymptomSensor(tracker),
    ]
    async_add_entities(entities)


class CareSensor(PetEntity, SensorEntity):
    """The next date of one care; for a sunny bath, the planned day once there is one."""

    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, tracker: PetTracker, care: dict[str, Any]) -> None:
        super().__init__(tracker, f"care_{care['key']}")
        self.care = care
        self._attr_name = care["name"]
        self._attr_icon = care.get("icon") or "mdi:paw"

    @property
    def native_value(self) -> date | None:
        state = self.tracker.care_state(self.care)
        if self.care.get("kind") == CARE_SUNNY and state["planned_day"]:
            return state["planned_day"]
        return state["next_due"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        state = self.tracker.care_state(self.care)
        return {
            "key": self.care["key"],
            "kind": self.care.get("kind"),
            "last_done": state["last_done"].isoformat() if state["last_done"] else None,
            "due": state["next_due"].isoformat() if state["next_due"] else None,
            "days_left": state["days_left"],
            "overdue": state["overdue"],
            "interval_days": state["interval_days"],
            "planned_day": state["planned_day"].isoformat() if state["planned_day"] else None,
            "plan_weather": state["plan_weather"],
        }


class MealSensor(PetEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["pending", *AMOUNTS]  # noqa: RUF012
    _attr_translation_key = "meal"
    _attr_icon = "mdi:bowl-mix"

    def __init__(self, tracker: PetTracker, meal: dict[str, Any]) -> None:
        super().__init__(tracker, f"meal_{meal['key']}")
        self.meal = meal
        self._attr_translation_placeholders = {"meal": meal["name"]}

    @property
    def native_value(self) -> str:
        entry = self.tracker.meal_today(self.meal["key"])
        return entry["value"] if entry else "pending"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        entry = self.tracker.meal_today(self.meal["key"]) or {}
        return {
            "time": self.meal["time"],
            "at": entry.get("at"),
            "grams": entry.get("grams"),
            "note": entry.get("note"),
            "by": entry.get("by"),
            **self.tracker.food(),
        }


class WeightSensor(PetEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_translation_key = "weight"
    _attr_suggested_display_precision = 1

    def __init__(self, tracker: PetTracker) -> None:
        super().__init__(tracker, "weight")

    @property
    def native_value(self) -> float | None:
        last = self.tracker.last_weight()
        return last["value"] if last else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        last = self.tracker.last_weight() or {}
        return {
            "at": last.get("at"),
            "history": [
                {"at": e["at"], "kg": e["value"]} for e in self.tracker.entries("weight")[-24:]
            ],
        }


class TreatmentsSensor(PetEntity, SensorEntity):
    _attr_translation_key = "treatments"
    _attr_icon = "mdi:medication"

    def __init__(self, tracker: PetTracker) -> None:
        super().__init__(tracker, "treatments")

    @property
    def native_value(self) -> int:
        return len(self.tracker.active_treatments())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        today = self.tracker.care_day()
        doses = self.tracker.doses_today()
        rows = []
        for t in self.tracker.treatments:
            mine = [d for d in doses if d["id"] == t["id"]]
            rows.append(
                {
                    **t,
                    "active": t in self.tracker.active_treatments(today),
                    "today": ", ".join(
                        f"{d['time']} {'✓' if d['status'] == 'given' else 'x' if d['status'] == 'skipped' else '·'}"
                        for d in mine
                    ),
                }
            )
        return {"treatments": sorted(rows, key=lambda r: (not r["active"], r.get("end") or "9999"))}


class NextDoseSensor(PetEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_translation_key = "next_dose"
    _attr_icon = "mdi:pill-multiple"

    def __init__(self, tracker: PetTracker) -> None:
        super().__init__(tracker, "next_dose")

    def _next(self) -> tuple[datetime, dict[str, Any]] | None:
        now = dt_util.now()
        best: tuple[datetime, dict[str, Any]] | None = None
        for offset in (0, 1):
            day = self.tracker.care_day() + timedelta(days=offset)
            for t in self.tracker.active_treatments(day):
                for at in t["times"]:
                    moment = datetime.combine(day, parse_time(at), tzinfo=now.tzinfo)
                    if offset == 0 and self.tracker.dose_status(t["id"], at) is not None:
                        continue
                    if (offset == 1 or moment >= now - timedelta(hours=2)) and (
                        best is None or moment < best[0]
                    ):
                        best = (moment, t)
            if best:
                break
        return best

    @property
    def native_value(self) -> datetime | None:
        found = self._next()
        return found[0] if found else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        found = self._next()
        return {"treatment": found[1]["name"], "dose": found[1].get("dose")} if found else {}


class LogSensor(PetEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_translation_key = "log"
    _attr_icon = "mdi:notebook-heart"

    def __init__(self, tracker: PetTracker) -> None:
        super().__init__(tracker, "log")

    @property
    def native_value(self) -> datetime | None:
        return dt_util.parse_datetime(self.tracker.log[-1]["at"]) if self.tracker.log else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "recent": self.tracker.recent(),
            "entries": len(self.tracker.log),
            "card": self._card(),
        }

    def _card(self) -> dict[str, Any]:
        """What the Pet Care card needs to draw this pet: ids, config and today's doses."""
        registry = er.async_get(self.hass)
        entry_id = self.tracker.entry_id

        def find(domain: str, key: str) -> str | None:
            return registry.async_get_entity_id(domain, DOMAIN, f"{entry_id}_{key}")

        tracker = self.tracker
        today = tracker.care_day()
        return {
            "entry_id": entry_id,
            "pet": tracker.pet,
            "sex": tracker.options.get("sex", "female"),
            "meals": [{**m, "entity": find("sensor", f"meal_{m['key']}")} for m in tracker.meals],
            "care": [
                {
                    "key": c["key"],
                    "name": c["name"],
                    "kind": c.get("kind"),
                    "icon": c.get("icon"),
                    "entity": find("sensor", f"care_{c['key']}"),
                    "button": find("button", f"done_{c['key']}"),
                }
                for c in tracker.care
            ],
            "doses": tracker.doses_today(),
            "treatments": [
                {k: t.get(k) for k in ("id", "name", "kind", "dose", "times", "start", "end")}
                for t in tracker.treatments
                if not t.get("ended") and (parse_date(t.get("end")) or today) >= today
            ],
            "upcoming": [
                {
                    "day": i["day"].isoformat(),
                    "summary": i["summary"].replace(f" · {tracker.pet}", ""),
                }
                for i in tracker.calendar_items()[:8]
            ],
            "weight": find("sensor", "weight"),
            "report": find("sensor", "report"),
            "shedding": find("switch", "shedding"),
            "plan": find("button", "plan_bath"),
            "food": tracker.food(),
        }


class ReportSensor(PetEntity, SensorEntity):
    """Symptoms in the last 30 days, with everything a vet asks about as attributes."""

    _attr_translation_key = "report"
    _attr_icon = "mdi:clipboard-pulse"

    def __init__(self, tracker: PetTracker) -> None:
        super().__init__(tracker, "report")

    @property
    def native_value(self) -> int:
        return sum(self.tracker.report()["symptoms"].values())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.tracker.report()


class SymptomSensor(PetEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_translation_key = "last_symptom"
    _attr_icon = "mdi:emoticon-sick-outline"

    def __init__(self, tracker: PetTracker) -> None:
        super().__init__(tracker, "last_symptom")

    @property
    def native_value(self) -> datetime | None:
        found = self.tracker.entries("symptom")
        return dt_util.parse_datetime(found[-1]["at"]) if found else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        found = self.tracker.entries("symptom")
        return {"symptom": found[-1]["value"], "note": found[-1].get("note")} if found else {}
