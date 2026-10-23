"""Constants for Pet Care."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "pet_care"
STORAGE_VERSION: Final = 1

CONF_PET_NAME: Final = "pet_name"
CONF_SPECIES: Final = "species"
CONF_WEATHER: Final = "weather_entity"
CONF_MEALS: Final = "meals"
CONF_FOOD: Final = "food"
CONF_FOOD_GRAMS: Final = "food_grams"
CONF_CARE: Final = "care"
CONF_REMINDER_TIME: Final = "reminder_time"
CONF_BATH_TIMES: Final = "bath_times"
CONF_PLAN_WEEKDAY: Final = "plan_weekday"
CONF_WEIGHT_DAY: Final = "weight_day"

SPECIES: Final = ["dog", "cat", "other"]

# Meals and doses are asked again this many minutes after their time while still open.
REPEAT_MINUTES: Final = (15, 30, 45)
# The day's meals and doses close at this hour; anything still open is logged as missed.
DAY_ROLLOVER_HOUR: Final = 4
# A meal logged without a slot belongs to the morning before this hour, to the evening after.
MORNING_UNTIL_HOUR: Final = 14

DEFAULT_MEALS: Final = [
    {"key": "morning", "name": "Manhã", "time": "07:45"},
    {"key": "evening", "name": "Noite", "time": "19:45"},
]
DEFAULT_REMINDER_TIME: Final = "09:00"
DEFAULT_BATH_TIMES: Final = ["10:00", "13:00", "15:00"]
DEFAULT_PLAN_WEEKDAY: Final = 0  # Monday
DEFAULT_PLAN_TIME: Final = "08:00"
DEFAULT_WEIGHT_DAY: Final = 1

# Care item kinds: a plain interval, a bath planned on the sunniest day, or grooming
# whose interval shortens while the coat is shedding.
CARE_INTERVAL: Final = "interval"
CARE_SUNNY: Final = "sunny"
CARE_SHEDDING: Final = "shedding"
CARE_KINDS: Final = [CARE_INTERVAL, CARE_SUNNY, CARE_SHEDDING]

AMOUNTS: Final = ["all", "half", "little", "none"]
SYMPTOMS: Final = [
    "vomit",
    "soft_stool",
    "diarrhea",
    "itching",
    "paw_licking",
    "red_eyes_ears",
    "no_appetite",
    "lethargy",
    "other",
]
TREATMENT_KINDS: Final = ["ointment", "spray", "pill", "drops", "shampoo", "injection", "other"]

# Months in which the coat usually starts or stops shedding: the pet's people are asked.
SHEDDING_ASK_MONTHS: Final = (3, 9)
SHEDDING_END_ASK_MONTHS: Final = (6, 12)

MAX_LOG: Final = 3000
RECENT_LOG: Final = 40
REPORT_DAYS: Final = 30

EVENT_REMINDER: Final = "pet_care_reminder"
EVENT_RESOLVED: Final = "pet_care_resolved"
ACTION_PREFIX: Final = "PETCARE"

SERVICE_LOG_CARE: Final = "log_care"
SERVICE_LOG_MEAL: Final = "log_meal"
SERVICE_LOG_SNACK: Final = "log_snack"
SERVICE_LOG_SYMPTOM: Final = "log_symptom"
SERVICE_LOG_WEIGHT: Final = "log_weight"
SERVICE_LOG_DOSE: Final = "log_dose"
SERVICE_ADD_TREATMENT: Final = "add_treatment"
SERVICE_UPDATE_TREATMENT: Final = "update_treatment"
SERVICE_END_TREATMENT: Final = "end_treatment"
SERVICE_SET_DUE: Final = "set_due"
SERVICE_DELETE_ENTRY: Final = "delete_entry"
SERVICE_UPDATE_ENTRY: Final = "update_entry"
SERVICE_EXPORT: Final = "export"

EXPORT_DIR: Final = "pet_care"


def signal_updated(entry_id: str) -> str:
    """Dispatcher signal for one pet's state changes."""
    return f"{DOMAIN}_updated_{entry_id}"


# What a correction may change in each kind of record, besides when it happened.
EDITABLE: Final = {
    "meal": {"meal", "amount", "grams", "note"},
    "snack": {"what", "grams", "note"},
    "symptom": {"symptom", "note"},
    "weight": {"kg", "note"},
    "care": {"note"},
    "dose": {"status"},
    "treatment": {"note"},
}
