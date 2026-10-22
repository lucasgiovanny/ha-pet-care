# Pet Care

A Home Assistant integration that keeps one record per pet: meals and how much was eaten,
care that comes round on a schedule (deworming, flea protection, bath, brushing), treatments
with their times and end date, symptoms and weight. Everything lives in Home Assistant's own
storage; nothing leaves your installation.

## What it gives you

For each pet, one device with:

| Entity | What it shows |
|---|---|
| `sensor.<pet>_<care>` | Next date of each care (last done, days left, overdue as attributes) |
| `binary_sensor.<pet>_<care>_late` | On when a care is overdue |
| `button.<pet>_<care>_done` | Records the care as done now |
| `sensor.<pet>_<meal>_meal` | Today's meal: pending, all, half, little or none |
| `sensor.<pet>_weight` | Last weigh-in, with the history as an attribute |
| `sensor.<pet>_treatments` | Active treatments, with today's doses |
| `sensor.<pet>_next_dose` | When the next dose is due |
| `sensor.<pet>_log` | The last 40 log entries (for a table card) |
| `sensor.<pet>_symptoms_in_30_days` | Symptom count, plus a 30-day report for the vet |
| `switch.<pet>_shedding_season` | Brushing comes round more often while on |
| `calendar.<pet>_care` | Upcoming care dates, planned baths and treatment ends |

## Care kinds

- **Every N days** — deworming, flea collar… Optional warning N days before.
- **Every N days at most, on the sunniest day** — a bath. On the planning day (Monday by
  default) the daily forecast of your weather entity picks the best day before the deadline;
  you are told which day, and reminded on that day.
- **Every N days, more often while shedding** — brushing, with a second interval used while
  the shedding switch is on. In March and September you are asked whether shedding started.

The log is the source of truth: deleting a wrong entry (`pet_care.delete_entry`) fixes the
dates derived from it.

## Reminders

The integration fires `pet_care_reminder` events (meals, doses, care, bath plan, weigh-in,
shedding question) with a title, message, a notification `tag` and ready-made actionable
notification buttons. Meals and doses repeat at 15, 30 and 45 minutes while still open.
When something is resolved it fires `pet_care_resolved` with the same `tag`, so you can
clear the notification everywhere. The buttons are handled by the integration itself
(`mobile_app_notification_action`), so an automation only has to deliver the notification:

```yaml
triggers:
  - trigger: event
    event_type: pet_care_reminder
    id: remind
  - trigger: event
    event_type: pet_care_resolved
    id: resolved
actions:
  - choose:
      - conditions: "{{ trigger.id == 'remind' }}"
        sequence:
          - action: notify.mobile_app_my_phone
            data:
              title: "{{ trigger.event.data.title }}"
              message: "{{ trigger.event.data.message }}"
              data:
                tag: "{{ trigger.event.data.tag }}"
                actions: "{{ trigger.event.data.actions }}"
      - conditions: "{{ trigger.id == 'resolved' }}"
        sequence:
          - action: notify.mobile_app_my_phone
            data:
              message: clear_notification
              data:
                tag: "{{ trigger.event.data.tag }}"
```

## Services

`log_care`, `log_meal`, `log_snack`, `log_symptom`, `log_weight`, `log_dose`,
`add_treatment`, `update_treatment`, `end_treatment`, `set_due`, `delete_entry` and
`export` (writes the whole log as CSV to the media folder). With a single pet the
`config_entry_id` field can be left out.

## Installation

HACS → Integrations → ⋮ → Custom repositories → add this repository as an Integration,
install **Pet Care**, restart, then add it from Settings → Devices & services.

## License

[MIT](LICENSE)
