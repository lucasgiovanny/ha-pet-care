"""One pet's record and reminders.

The log is the single source of truth: when care was last done, what was eaten
today and which doses were given are all read back from it, so deleting a wrong
entry fixes everything derived from it. The store adds only what the log cannot
hold: due dates set by hand, the shedding flag, treatments and bath plans.
"""

from __future__ import annotations

import csv
import io
import logging
import os
from collections import Counter
from datetime import date, datetime, timedelta
from typing import Any

from homeassistant.core import CALLBACK_TYPE, Context, Event, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
from homeassistant.util import ulid as ulid_util

from .const import (
    ACTION_PREFIX,
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
    CONF_WEATHER,
    CONF_WEIGHT_DAY,
    DAY_ROLLOVER_HOUR,
    DEFAULT_BATH_TIMES,
    DEFAULT_MEALS,
    DEFAULT_PLAN_TIME,
    DEFAULT_PLAN_WEEKDAY,
    DEFAULT_REMINDER_TIME,
    DEFAULT_WEIGHT_DAY,
    DOMAIN,
    EDITABLE,
    EVENT_REMINDER,
    EVENT_RESOLVED,
    EXPORT_DIR,
    MAX_LOG,
    RECENT_LOG,
    REPORT_DAYS,
    SHEDDING_ASK_MONTHS,
    SHEDDING_END_ASK_MONTHS,
    STORAGE_VERSION,
    signal_updated,
)
from .logic import (
    care_interval,
    care_next_due,
    care_reminder,
    day_of,
    meal_slot_for,
    parse_date,
    parse_time,
    plan_bath,
    repeat_index,
    treatment_active_on,
)
from .texts import texts

_LOGGER = logging.getLogger(__name__)


def _when(value: str) -> datetime:
    """A stored ISO timestamp, as an aware datetime."""
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        raise ValueError(f"Bad timestamp {value}")
    return parsed


SAVE_DELAY_SECONDS = 2.0
ALL_TREATMENTS = {"all", "*", "todos", "todas"}


class PetTracker:
    """Owns everything Home Assistant knows about one pet."""

    def __init__(self, hass: HomeAssistant, entry_id: str, options: dict[str, Any]) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.options = options
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}")
        self.log: list[dict[str, Any]] = []
        self.due_overrides: dict[str, str] = {}
        self.shedding = False
        self.treatments: list[dict[str, Any]] = []
        self.bath_plans: dict[str, dict[str, Any]] = {}
        self._unsubs: list[CALLBACK_TYPE] = []

    # ---- configuration -------------------------------------------------

    @property
    def pet(self) -> str:
        return self.options[CONF_PET_NAME]

    @property
    def meals(self) -> list[dict[str, Any]]:
        return self.options.get(CONF_MEALS) or DEFAULT_MEALS

    @property
    def care(self) -> list[dict[str, Any]]:
        return self.options.get(CONF_CARE) or []

    def care_item(self, key: str) -> dict[str, Any]:
        for care in self.care:
            if care["key"] == key or care["name"].lower() == str(key).lower():
                return care
        raise ServiceValidationError(f"Unknown care: {key}")

    @property
    def t(self) -> dict[str, Any]:
        return texts(self.hass.config.language)

    def _fmt(self, key: str, **values: Any) -> str:
        female = self.options.get("sex", "female") == "female"
        return self.t[key].format(
            pet=self.pet,
            da="da" if female else "do",
            a="a" if female else "o",
            A="A" if female else "O",
            **values,
        )

    # ---- lifecycle -----------------------------------------------------

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.log = data.get("log", [])
        self.due_overrides = data.get("due_overrides", {})
        self.shedding = data.get("shedding", False)
        self.treatments = data.get("treatments", [])
        self.bath_plans = data.get("bath_plans", {})
        for treatment in self.treatments:
            # Treatments from 0.1.2 and earlier: their start is in the log.
            if "created" not in treatment:
                started = [
                    e
                    for e in self.entries("treatment", treatment["id"])
                    if str(e.get("value", "")).startswith("start")
                ]
                if started:
                    treatment["created"] = started[0]["at"]

    def _data(self) -> dict[str, Any]:
        return {
            "log": self.log,
            "due_overrides": self.due_overrides,
            "shedding": self.shedding,
            "treatments": self.treatments,
            "bath_plans": self.bath_plans,
        }

    @callback
    def async_start(self) -> None:
        self._unsubs.append(async_track_time_change(self.hass, self._async_tick, second=0))
        self._unsubs.append(
            self.hass.bus.async_listen("mobile_app_notification_action", self._async_action)
        )

    @callback
    def async_stop(self) -> None:
        while self._unsubs:
            self._unsubs.pop()()

    @callback
    def _changed(self) -> None:
        self._store.async_delay_save(self._data, SAVE_DELAY_SECONDS)
        async_dispatcher_send(self.hass, signal_updated(self.entry_id))

    async def async_flush(self) -> None:
        await self._store.async_save(self._data())

    # ---- the log -------------------------------------------------------

    async def _by(self, context: Context | None) -> str | None:
        if context is None or context.user_id is None:
            return None
        user = await self.hass.auth.async_get_user(context.user_id)
        return user.name if user else None

    def _append(self, entry: dict[str, Any]) -> dict[str, Any]:
        entry = {
            "id": ulid_util.ulid_now(),
            **{k: v for k, v in entry.items() if v not in (None, "")},
        }
        self.log.append(entry)
        self.log.sort(key=lambda e: e["at"])
        del self.log[:-MAX_LOG]
        return entry

    def entries(self, kind: str | None = None, key: str | None = None) -> list[dict[str, Any]]:
        return [
            e
            for e in self.log
            if (kind is None or e["type"] == kind) and (key is None or e.get("key") == key)
        ]

    @staticmethod
    def _at(at: datetime | None) -> datetime:
        return dt_util.as_local(at) if at else dt_util.now()

    async def async_delete(self, entry_id: str) -> None:
        before = len(self.log)
        self.log = [e for e in self.log if e["id"] != entry_id]
        if len(self.log) == before:
            raise ServiceValidationError(f"No log entry {entry_id}")
        self._changed()

    async def async_update(self, entry_id: str, changes: dict[str, Any]) -> None:
        """Correct a record: when it happened and what its type records; None clears grams or note."""
        entry = next((e for e in self.log if e["id"] == entry_id), None)
        if entry is None:
            raise ServiceValidationError(f"No log entry {entry_id}")
        unknown = set(changes) - EDITABLE.get(entry["type"], set()) - {"at"}
        if unknown:
            raise ServiceValidationError(
                f"A {entry['type']} record has no {', '.join(sorted(unknown))}"
            )
        if changes.get("at"):
            entry["at"] = self._at(changes["at"]).isoformat()
        if "meal" in changes:
            key = self._meal_key(changes["meal"])
            if key is None:
                raise ServiceValidationError(f"No meal {changes['meal']}")
            entry["key"] = key
        if "symptom" in changes:
            entry["key"] = changes["symptom"]
            entry["value"] = self.t["symptom"].get(changes["symptom"], changes["symptom"])
        for field in ("amount", "what", "status"):
            if field in changes:
                entry["value"] = changes[field]
        if "kg" in changes:
            entry["value"] = round(float(changes["kg"]), 2)
        for field in ("grams", "note"):
            if field in changes and changes[field] in (None, ""):
                entry.pop(field, None)
            elif field in changes:
                entry[field] = changes[field]
        self.log.sort(key=lambda e: e["at"])
        self._changed()

    # ---- care ----------------------------------------------------------

    def last_done(self, key: str) -> date | None:
        done = self.entries("care", key)
        return _when(done[-1]["at"]).date() if done else None

    def care_state(self, care: dict[str, Any]) -> dict[str, Any]:
        """Everything a card shows about one care: last, next, days left, plan."""
        state = {
            **care,
            "last_done": self.last_done(care["key"]),
            "next_due": self.due_overrides.get(care["key"]),
        }
        due = care_next_due({**state, "last_done": state["last_done"]}, self.shedding)
        today = dt_util.now().date()
        plan = self.bath_plans.get(care["key"])
        return {
            "last_done": state["last_done"],
            "next_due": due,
            "days_left": (due - today).days if due else None,
            "overdue": bool(due and today > due),
            "interval_days": care_interval(care, self.shedding),
            "planned_day": parse_date(plan["day"]) if plan else None,
            "plan_weather": plan.get("weather") if plan else None,
        }

    async def async_log_care(
        self,
        key: str,
        at: datetime | None = None,
        note: str | None = None,
        context: Context | None = None,
    ) -> None:
        care = self.care_item(key)
        moment = self._at(at)
        self._append(
            {
                "type": "care",
                "key": care["key"],
                "value": care["name"],
                "at": moment.isoformat(),
                "note": note,
                "by": await self._by(context),
            }
        )
        # Doing it, early or late, starts the interval again from today.
        self.due_overrides.pop(care["key"], None)
        self.bath_plans.pop(care["key"], None)
        self._resolve(f"care-{care['key']}")
        self._changed()

    async def async_set_due(self, key: str, day: date) -> None:
        care = self.care_item(key)
        self.due_overrides[care["key"]] = day.isoformat()
        self._changed()

    def set_shedding(self, on: bool) -> None:
        self.shedding = on
        self._resolve("shedding")
        self._changed()

    # ---- meals ---------------------------------------------------------

    def care_day(self, moment: datetime | None = None) -> date:
        return day_of(moment or dt_util.now(), DAY_ROLLOVER_HOUR)

    def meal_today(self, slot: str) -> dict[str, Any] | None:
        today = self.care_day()
        found = [
            e
            for e in self.entries("meal", slot)
            if self.care_day(dt_util.as_local(_when(e["at"]))) == today
        ]
        return found[-1] if found else None

    def _meal_key(self, slot: str | None) -> str | None:
        """A meal's key from its key or its name."""
        if slot in {m["key"] for m in self.meals}:
            return slot
        return {m["name"].lower(): m["key"] for m in self.meals}.get(str(slot or "").lower())

    async def async_log_meal(
        self,
        slot: str | None,
        amount: str,
        grams: float | None = None,
        note: str | None = None,
        at: datetime | None = None,
        context: Context | None = None,
    ) -> None:
        moment = self._at(at)
        slot = self._meal_key(slot) or meal_slot_for(moment, self.meals)
        self._append(
            {
                "type": "meal",
                "key": slot,
                "value": amount,
                "grams": grams,
                "note": note,
                "at": moment.isoformat(),
                "by": await self._by(context),
            }
        )
        self._resolve(f"meal-{slot}")
        self._changed()

    async def async_log_snack(
        self,
        what: str,
        grams: float | None = None,
        note: str | None = None,
        at: datetime | None = None,
        context: Context | None = None,
    ) -> None:
        self._append(
            {
                "type": "snack",
                "value": what,
                "grams": grams,
                "note": note,
                "at": self._at(at).isoformat(),
                "by": await self._by(context),
            }
        )
        self._changed()

    # ---- health --------------------------------------------------------

    async def async_log_symptom(
        self,
        symptom: str,
        note: str | None = None,
        at: datetime | None = None,
        context: Context | None = None,
    ) -> None:
        self._append(
            {
                "type": "symptom",
                "key": symptom,
                "value": self.t["symptom"].get(symptom, symptom),
                "note": note,
                "at": self._at(at).isoformat(),
                "by": await self._by(context),
            }
        )
        self._changed()

    async def async_log_weight(
        self,
        kg: float,
        note: str | None = None,
        at: datetime | None = None,
        context: Context | None = None,
    ) -> None:
        self._append(
            {
                "type": "weight",
                "value": round(float(kg), 2),
                "note": note,
                "at": self._at(at).isoformat(),
                "by": await self._by(context),
            }
        )
        self._resolve("weight")
        self._changed()

    def last_weight(self) -> dict[str, Any] | None:
        weights = self.entries("weight")
        return weights[-1] if weights else None

    # ---- treatments ----------------------------------------------------

    def treatment(self, ref: str) -> dict[str, Any]:
        for treatment in self.treatments:
            if treatment["id"] == ref or treatment["name"].lower() == str(ref).lower():
                return treatment
        raise ServiceValidationError(f"Unknown treatment: {ref}")

    def active_treatments(self, day: date | None = None) -> list[dict[str, Any]]:
        day = day or self.care_day()
        return [t for t in self.treatments if treatment_active_on(t, day)]

    async def async_add_treatment(
        self, data: dict[str, Any], context: Context | None = None
    ) -> dict[str, Any]:
        treatment = {
            "id": ulid_util.ulid_now()[-8:].lower(),
            "name": data["name"],
            "kind": data.get("kind", "other"),
            "dose": data.get("dose"),
            "times": sorted(str(t)[:5] for t in data["times"]),
            "start": (data.get("start") or dt_util.now().date()).isoformat(),
            "end": data["end"].isoformat() if data.get("end") else None,
            "ended": False,
            "created": dt_util.now().isoformat(),
        }
        self.treatments.append(treatment)
        self._append(
            {
                "type": "treatment",
                "key": treatment["id"],
                "value": f"start: {treatment['name']}",
                "note": data.get("note"),
                "at": dt_util.now().isoformat(),
                "by": await self._by(context),
            }
        )
        self._changed()
        return treatment

    async def async_update_treatment(self, ref: str, data: dict[str, Any]) -> None:
        treatment = self.treatment(ref)
        for key in ("name", "kind", "dose"):
            if data.get(key) is not None:
                treatment[key] = data[key]
        if data.get("times"):
            treatment["times"] = sorted(str(t)[:5] for t in data["times"])
        if data.get("start"):
            treatment["start"] = data["start"].isoformat()
        if "end" in data:
            treatment["end"] = data["end"].isoformat() if data["end"] else None
        self._changed()

    async def async_end_treatment(self, ref: str, context: Context | None = None) -> None:
        treatment = self.treatment(ref)
        treatment["ended"] = True
        treatment["end"] = min(
            parse_date(treatment.get("end")) or date.max, dt_util.now().date()
        ).isoformat()
        self._append(
            {
                "type": "treatment",
                "key": treatment["id"],
                "value": f"end: {treatment['name']}",
                "at": dt_util.now().isoformat(),
                "by": await self._by(context),
            }
        )
        self._changed()

    def dose_status(self, treatment_id: str, at_time: str, day: date | None = None) -> str | None:
        entry = self.dose_entry(treatment_id, at_time, day)
        return entry["value"] if entry else None

    def dose_times(self, treatment: dict[str, Any], day: date) -> list[str]:
        """A treatment's times on a day, without the ones already past when it was created."""
        created = treatment.get("created")
        if not created:
            return list(treatment["times"])
        made = dt_util.as_local(_when(created))
        if self.care_day(made) != day:
            return list(treatment["times"])
        return [
            at
            for at in treatment["times"]
            if datetime.combine(day, parse_time(at), tzinfo=made.tzinfo)
            >= made - timedelta(minutes=30)
        ]

    def dose_entry(
        self, treatment_id: str, at_time: str, day: date | None = None
    ) -> dict[str, Any] | None:
        day = day or self.care_day()
        key = f"{treatment_id}@{at_time}"
        found = [
            e
            for e in self.entries("dose", key)
            if self.care_day(dt_util.as_local(_when(e["at"]))) == day
        ]
        return found[-1] if found else None

    def doses_today(self) -> list[dict[str, Any]]:
        rows = []
        for t in self.active_treatments():
            for at in self.dose_times(t, self.care_day()):
                entry = self.dose_entry(t["id"], at) or {}
                rows.append(
                    {
                        "treatment": t["name"],
                        "id": t["id"],
                        "kind": t.get("kind"),
                        "dose": t.get("dose"),
                        "time": at,
                        "status": entry.get("value"),
                        "at": entry.get("at"),
                        "by": entry.get("by"),
                        "entry": entry.get("id"),
                    }
                )
        return sorted(rows, key=lambda r: (r["time"], r["treatment"]))

    async def async_log_dose(
        self,
        ref: str,
        status: str = "given",
        at_time: str | None = None,
        context: Context | None = None,
    ) -> None:
        if str(ref).lower() in ALL_TREATMENTS:
            # Every dose still open from 3 h ago to 3 h ahead: "I gave the medicines now".
            now = dt_util.now()
            for dose in self.doses_today():
                at = parse_time(dose["time"])
                moment = now.replace(hour=at.hour, minute=at.minute)
                if dose["status"] is None and abs((now - moment).total_seconds()) <= 3 * 3600:
                    await self.async_log_dose(dose["id"], status, dose["time"], context)
            return
        treatment = self.treatment(ref)
        now = dt_util.now()
        if at_time is None:
            # The open dose closest to now; past ones first, so a late dose counts for its own slot.
            open_times = [
                at for at in treatment["times"] if self.dose_status(treatment["id"], at) is None
            ]
            if not open_times:
                open_times = treatment["times"]
            at_time = min(
                open_times,
                key=lambda at: abs(
                    (
                        now - now.replace(hour=parse_time(at).hour, minute=parse_time(at).minute)
                    ).total_seconds()
                ),
            )
        at_time = str(at_time)[:5]
        self._append(
            {
                "type": "dose",
                "key": f"{treatment['id']}@{at_time}",
                "value": status,
                "note": treatment["name"],
                "at": now.isoformat(),
                "by": await self._by(context),
            }
        )
        self._resolve(f"dose-{treatment['id']}-{at_time}")
        self._changed()

    # ---- reminders -----------------------------------------------------

    def _remind(
        self,
        kind: str,
        key: str,
        tag: str,
        title: str,
        message: str,
        actions: list[dict[str, Any]],
        repeat: int = 0,
    ) -> None:
        self.hass.bus.async_fire(
            EVENT_REMINDER,
            {
                "entry_id": self.entry_id,
                "pet": self.pet,
                "kind": kind,
                "key": key,
                "tag": f"petcare-{self.entry_id[-6:]}-{tag}",
                "title": title,
                "message": message,
                "actions": actions,
                "repeat": repeat,
            },
        )

    def _resolve(self, tag: str) -> None:
        self.hass.bus.async_fire(
            EVENT_RESOLVED,
            {"entry_id": self.entry_id, "tag": f"petcare-{self.entry_id[-6:]}-{tag}"},
        )

    def _action(self, *parts: str) -> str:
        return "|".join((ACTION_PREFIX, self.entry_id, *parts))

    async def _async_tick(self, now: datetime) -> None:
        now = dt_util.as_local(now)
        try:
            await self._async_run_minute(now)
        except Exception:
            _LOGGER.exception("Pet Care reminder check failed")

    async def _async_run_minute(self, now: datetime) -> None:
        today = self.care_day(now)
        if now.hour == DAY_ROLLOVER_HOUR and now.minute == 0:
            self._rollover(now)

        for meal in self.meals:
            repeat = repeat_index(now, parse_time(meal["time"]))
            if repeat is not None and self.meal_today(meal["key"]) is None:
                self._remind(
                    "meal",
                    meal["key"],
                    f"meal-{meal['key']}",
                    self._fmt("meal_title"),
                    self._fmt("meal_message", meal=meal["name"]),
                    [
                        {"action": self._action("meal", meal["key"], amount), "title": title}
                        for amount, title in self.t["amount"].items()
                    ],
                    repeat,
                )

        for treatment in self.active_treatments(today):
            for at in self.dose_times(treatment, today):
                repeat = repeat_index(now, parse_time(at))
                if repeat is not None and self.dose_status(treatment["id"], at) is None:
                    message = self._fmt("dose_message", name=treatment["name"], time=at)
                    if treatment.get("dose"):
                        message += self.t["dose_dose"].format(dose=treatment["dose"])
                    self._remind(
                        "dose",
                        treatment["id"],
                        f"dose-{treatment['id']}-{at}",
                        self._fmt("dose_title"),
                        message,
                        [
                            {
                                "action": self._action("dose", f"{treatment['id']}@{at}", "given"),
                                "title": self.t["gave"],
                            },
                            {
                                "action": self._action(
                                    "dose", f"{treatment['id']}@{at}", "skipped"
                                ),
                                "title": self.t["skip"],
                            },
                        ],
                        repeat,
                    )

        reminder = parse_time(self.options.get(CONF_REMINDER_TIME) or DEFAULT_REMINDER_TIME)
        if now.hour == reminder.hour and now.minute == reminder.minute:
            self._daily_reminders(now.date())

        plan_at = parse_time(DEFAULT_PLAN_TIME)
        if now.hour == plan_at.hour and now.minute == plan_at.minute:
            await self._async_plan_baths(
                now.date(),
                announce=now.weekday()
                == int(self.options.get(CONF_PLAN_WEEKDAY, DEFAULT_PLAN_WEEKDAY)),
            )

        for care in self.care:
            plan = self.bath_plans.get(care["key"])
            if care.get("kind") != CARE_SUNNY or not plan or parse_date(plan["day"]) != now.date():
                continue
            for at in self.options.get(CONF_BATH_TIMES) or DEFAULT_BATH_TIMES:
                if repeat_index(now, parse_time(at)) == 0:
                    self._remind(
                        "care",
                        care["key"],
                        f"care-{care['key']}",
                        self._fmt("care_title"),
                        self._fmt(
                            "bath_today",
                            care_l=care["name"].lower(),
                            weather=self._weather_text(plan.get("weather")),
                        ),
                        [
                            {
                                "action": self._action("care", care["key"], "done"),
                                "title": self.t["done"],
                            }
                        ],
                    )

    @callback
    def _rollover(self, now: datetime) -> None:
        yesterday = self.care_day(now - timedelta(hours=1))
        for treatment in self.treatments:
            if not treatment_active_on(treatment, yesterday):
                continue
            for at in self.dose_times(treatment, yesterday):
                if self.dose_status(treatment["id"], at, yesterday) is None:
                    moment = datetime.combine(yesterday, parse_time(at), tzinfo=now.tzinfo)
                    self._append(
                        {
                            "type": "dose",
                            "key": f"{treatment['id']}@{at}",
                            "value": "missed",
                            "note": treatment["name"],
                            "at": moment.isoformat(),
                        }
                    )
        for treatment in self.treatments:
            end = parse_date(treatment.get("end"))
            if not treatment.get("ended") and end and end < now.date():
                treatment["ended"] = True
                self._append(
                    {
                        "type": "treatment",
                        "key": treatment["id"],
                        "value": f"end: {treatment['name']}",
                        "at": now.isoformat(),
                    }
                )
        self._changed()

    def _daily_reminders(self, today: date) -> None:
        for care in self.care:
            state = self.care_state(care)
            kind = care_reminder(
                {
                    **care,
                    "last_done": state["last_done"],
                    "next_due": self.due_overrides.get(care["key"]),
                },
                today,
                self.shedding,
            )
            # A sunny care has its own day; the daily reminder only chases it once it is late.
            if kind is None or (care.get("kind") == CARE_SUNNY and kind != "overdue"):
                continue
            due = state["next_due"]
            days = abs((due - today).days)
            if kind == "lead":
                message = (
                    self._fmt("care_lead_one", care=care["name"], care_l=care["name"].lower())
                    if days == 1
                    else self._fmt(
                        "care_lead",
                        care=care["name"],
                        care_l=care["name"].lower(),
                        days=days,
                        date=due.strftime("%d/%m"),
                    )
                )
            else:
                message = self._fmt(
                    f"care_{kind}", care=care["name"], care_l=care["name"].lower(), days=days
                )
            self._remind(
                "care",
                care["key"],
                f"care-{care['key']}",
                self._fmt("care_title"),
                message,
                [{"action": self._action("care", care["key"], "done"), "title": self.t["done"]}],
            )

        last = self.last_weight()
        weigh_day = int(self.options.get(CONF_WEIGHT_DAY, DEFAULT_WEIGHT_DAY))
        if today.day == weigh_day and (
            last is None or (dt_util.now() - _when(last["at"])).days >= 20
        ):
            self._remind(
                "weight",
                "weight",
                "weight",
                self._fmt("weight_title"),
                self._fmt("weight_message"),
                [
                    {
                        "action": self._action("weight"),
                        "title": "kg",
                        "behavior": "textInput",
                        "textInputButtonTitle": "OK",
                        "textInputPlaceholder": "kg",
                    }
                ],
            )

        if today.day == 1 and any(c.get("kind") == CARE_SHEDDING for c in self.care):
            if today.month in SHEDDING_ASK_MONTHS and not self.shedding:
                question = "shedding_start"
            elif today.month in SHEDDING_END_ASK_MONTHS and self.shedding:
                question = "shedding_end"
            else:
                question = None
            if question:
                on = question == "shedding_start"
                self._remind(
                    "shedding",
                    "shedding",
                    "shedding",
                    self._fmt("shedding_title"),
                    self._fmt(question),
                    [
                        {
                            "action": self._action("shedding", "on" if on else "off"),
                            "title": self.t["yes"],
                        },
                        {
                            "action": self._action("shedding", "off" if on else "on"),
                            "title": self.t["no"],
                        },
                    ],
                )

    async def _async_forecast(self) -> list[dict[str, Any]]:
        entity = self.options.get(CONF_WEATHER)
        if not entity or self.hass.states.get(entity) is None:
            return []
        try:
            response = await self.hass.services.async_call(
                "weather",
                "get_forecasts",
                {"entity_id": entity, "type": "daily"},
                blocking=True,
                return_response=True,
            )
        except Exception:
            _LOGGER.warning("Could not read the daily forecast of %s", entity)
            return []
        result: dict[str, Any] = dict(response or {})
        return list((result.get(entity) or {}).get("forecast", []))

    async def async_plan_baths(self, announce: bool = True) -> None:
        await self._async_plan_baths(dt_util.now().date(), announce, force=True)

    async def _async_plan_baths(self, today: date, announce: bool, force: bool = False) -> None:
        sunny = [c for c in self.care if c.get("kind") == CARE_SUNNY]
        if not sunny:
            return
        forecasts = await self._async_forecast()
        for care in sunny:
            old = self.bath_plans.get(care["key"])
            if old is None and not announce and not force:
                continue
            last = self.last_done(care["key"])
            due = care_next_due(
                {**care, "last_done": last, "next_due": self.due_overrides.get(care["key"])},
                self.shedding,
            )
            deadline = due or today + timedelta(days=6 - today.weekday())
            day, forecast = plan_bath(today, deadline, forecasts)
            weather = (
                {"condition": forecast.get("condition"), "temperature": forecast.get("temperature")}
                if forecast
                else None
            )
            self.bath_plans[care["key"]] = {
                "day": day.isoformat(),
                "deadline": deadline.isoformat(),
                "weather": weather,
                "made": today.isoformat(),
            }
            changed = old is not None and old.get("day") != day.isoformat()
            if announce or changed:
                text = "bath_changed" if changed and not announce else "bath_plan"
                suffix = self.t["bath_deadline"] if day == deadline and forecast is None else ""
                self._remind(
                    "plan",
                    care["key"],
                    f"plan-{care['key']}",
                    self._fmt("care_title"),
                    self._fmt(
                        text,
                        care_l=care["name"].lower(),
                        day=self._day_text(day, today),
                        weather=self._weather_text(weather),
                    )
                    + suffix,
                    [],
                )
        self._changed()

    def _day_text(self, day: date, today: date) -> str:
        if day == today:
            return self.t["today"]
        if day == today + timedelta(days=1):
            return self.t["tomorrow"]
        return f"{self.t['weekday'][day.weekday()]} ({day.strftime('%d/%m')})"

    def _weather_text(self, weather: dict[str, Any] | None) -> str:
        if not weather:
            return ""
        bits = []
        if weather.get("temperature") is not None:
            bits.append(f"{round(weather['temperature'])} °C")
        if weather.get("condition"):
            bits.append(self.t["condition"].get(weather["condition"], weather["condition"]))
        return f" ({', '.join(bits)})" if bits else ""

    async def _async_action(self, event: Event) -> None:
        action = str(event.data.get("action", ""))
        parts = action.split("|")
        if len(parts) < 3 or parts[0] != ACTION_PREFIX or parts[1] != self.entry_id:
            return
        verb, args = parts[2], parts[3:]
        try:
            if verb == "meal":
                await self.async_log_meal(args[0], args[1], context=event.context)
            elif verb == "dose":
                treatment_id, at_time = args[0].split("@")
                await self.async_log_dose(treatment_id, args[1], at_time, context=event.context)
            elif verb == "care":
                await self.async_log_care(args[0], context=event.context)
            elif verb == "shedding":
                self.set_shedding(args[0] == "on")
            elif verb == "weight":
                text = (
                    str(event.data.get("reply_text", ""))
                    .replace(",", ".")
                    .replace("kg", "")
                    .strip()
                )
                await self.async_log_weight(float(text), context=event.context)
        except (ValueError, IndexError, ServiceValidationError) as err:
            _LOGGER.warning("Ignored notification action %s: %s", action, err)

    # ---- views ---------------------------------------------------------

    def recent(self, count: int = RECENT_LOG) -> list[dict[str, Any]]:
        amounts = self.t["amount"]
        meals = {m["key"]: m["name"] for m in self.meals}
        rows = []
        for entry in reversed(self.log[-count:]):
            row = dict(entry)
            if entry["type"] == "meal":
                row["label"] = (
                    f"{meals.get(entry.get('key'), entry.get('key'))}: {amounts.get(entry['value'], entry['value'])}"
                )
            elif entry["type"] == "dose":
                status = self.t["dose_status"].get(entry["value"], entry["value"])
                row["label"] = f"{entry.get('note', '')}: {status}"
            elif entry["type"] == "treatment":
                verb, _, name = str(entry.get("value", "")).partition(": ")
                row["label"] = (
                    f"{self.t['treatment_start' if verb == 'start' else 'treatment_end']}: {name}"
                )
            elif entry["type"] == "weight":
                row["label"] = f"{entry['value']} kg"
            else:
                row["label"] = str(entry.get("value", ""))
            rows.append(row)
        return rows

    def report(self, days: int = REPORT_DAYS) -> dict[str, Any]:
        since = dt_util.now() - timedelta(days=days)
        window = [e for e in self.log if _when(e["at"]) >= since]
        symptoms = [e for e in window if e["type"] == "symptom"]
        meals = [e for e in window if e["type"] == "meal"]
        doses = [e for e in window if e["type"] == "dose"]
        weights = [e for e in window if e["type"] == "weight"]
        dose_count: dict[str, Counter[str]] = {}
        for dose in doses:
            dose_count.setdefault(dose.get("note", "?"), Counter())[dose["value"]] += 1
        return {
            "days": days,
            "symptoms": dict(Counter(e["value"] for e in symptoms)),
            "symptom_list": [
                {"at": e["at"], "symptom": e["value"], "note": e.get("note")} for e in symptoms
            ],
            "meals": dict(Counter(e["value"] for e in meals)),
            "snacks": [
                {"at": e["at"], "what": e["value"], "grams": e.get("grams"), "note": e.get("note")}
                for e in window
                if e["type"] == "snack"
            ],
            "doses": {name: dict(c) for name, c in dose_count.items()},
            "weight_start": weights[0]["value"] if weights else None,
            "weight_end": weights[-1]["value"] if weights else None,
        }

    def calendar_items(self) -> list[dict[str, Any]]:
        """Upcoming dates: care due, planned baths, treatment ends, the weigh-in."""
        items = []
        for care in self.care:
            state = self.care_state(care)
            if state["planned_day"]:
                items.append(
                    {
                        "day": state["planned_day"],
                        "summary": f"{care['name']} · {self.pet}",
                        "uid": f"plan-{care['key']}",
                    }
                )
            elif state["next_due"]:
                items.append(
                    {
                        "day": state["next_due"],
                        "summary": f"{care['name']} · {self.pet}",
                        "uid": f"care-{care['key']}",
                    }
                )
        for treatment in self.treatments:
            end = parse_date(treatment.get("end"))
            if end and not treatment.get("ended"):
                items.append(
                    {
                        "day": end,
                        "summary": f"{treatment['name']} (fim) · {self.pet}",
                        "uid": f"end-{treatment['id']}",
                    }
                )
        today = dt_util.now().date()
        weigh_day = int(self.options.get(CONF_WEIGHT_DAY, DEFAULT_WEIGHT_DAY))
        next_weigh = (
            today.replace(day=weigh_day)
            if today.day <= weigh_day
            else (today.replace(day=1) + timedelta(days=32)).replace(day=weigh_day)
        )
        items.append(
            {"day": next_weigh, "summary": f"{self.t['weigh_in']} · {self.pet}", "uid": "weight"}
        )
        return sorted(items, key=lambda i: i["day"])

    def food(self) -> dict[str, Any]:
        return {
            "food": self.options.get(CONF_FOOD),
            "food_grams": self.options.get(CONF_FOOD_GRAMS),
        }

    # ---- export --------------------------------------------------------

    async def async_export(self) -> dict[str, Any]:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["at", "type", "key", "value", "grams", "note", "by"])
        for entry in self.log:
            writer.writerow(
                [
                    entry["at"],
                    entry["type"],
                    entry.get("key", ""),
                    entry.get("value", ""),
                    entry.get("grams", ""),
                    entry.get("note", ""),
                    entry.get("by", ""),
                ]
            )
        content = buffer.getvalue()
        media = self.hass.config.media_dirs.get("local") or self.hass.config.path("media")
        folder = os.path.join(media, EXPORT_DIR)
        name = f"{self.pet.lower().replace(' ', '_')}-{dt_util.now().strftime('%Y%m%d-%H%M')}.csv"
        path = os.path.join(folder, name)

        def _write() -> None:
            os.makedirs(folder, exist_ok=True)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(content)

        await self.hass.async_add_executor_job(_write)
        return {
            "path": path,
            "media": f"media-source://media_source/local/{EXPORT_DIR}/{name}",
            "rows": len(self.log),
        }
