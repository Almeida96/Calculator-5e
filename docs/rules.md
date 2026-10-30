# Rules and calculation assumptions

The rule reference is the [2014 Basic Rules, Adventuring](https://www.dndbeyond.com/sources/dnd/basic-rules-2014/adventuring#TravelPace), also published in [SRD 5.1](https://media.dndbeyond.com/compendium-images/srd/5.1/SRD_CC_v5.1.pdf). See [attribution](../NOTICE.md).

## Travel pace

| Pace | Miles per hour | Miles per eight-hour day | Effect |
| --- | ---: | ---: | --- |
| Slow | 2 | 18 | Permits stealth |
| Normal | 3 | 24 | No pace modifier |
| Fast | 4 | 30 | −5 to passive Wisdom (Perception) |

Difficult terrain halves travel speed. The planner applies that multiplier separately to each leg.

## Daily and hourly bases

The table's columns are not exact multiples. Both are preserved:

- **Daily**, the default: divide the daily distance by eight for the first eight travel hours of each day. After eight hours, use the hourly column.
- **Hourly**: use the hourly column throughout the day.

Daily interpolation is this application's planning convention for partial days and mixed terrain. It is not a claim that the rules specify an exact minute of arrival.

Examples on normal terrain:

| Journey | Basis | Result |
| --- | --- | --- |
| 30 mi, fast, 8 hours/day | Daily | 1 day, 8 moving hours |
| 30 mi, fast, 8 hours/day | Hourly | 1 day, 7.5 moving hours |
| 18 mi, slow, 8 hours/day | Daily | 1 day, 8 moving hours |
| 18 mi, slow, 8 hours/day | Hourly | 2 days, 9 moving hours |
| 38 mi, fast, 10 hours/day | Daily | 1 day: 30 mi in 8 hours, then 8 mi in 2 hours |

Hours carry across leg boundaries. A road-to-forest transition does not start a new day or reset forced-march time.

## Forced march

At the end of each completed travel hour beyond eight, list a Constitution save with DC 10 plus the number of hours beyond eight: DC 11 after hour nine, DC 12 after hour ten, and so on. The count restarts each travel day.

A journey ending after 8.5 moving hours lists no additional save; the DM can apply a different ruling for incomplete hours. The planner does not roll saves, apply exhaustion or recalculate speed after a failed save. Later travel estimates therefore assume no movement penalty from exhaustion.

## Units and custom speeds

One mile is converted to exactly 1.609344 kilometers. Calculations use rational arithmetic; output is rounded only for display.

Custom speed uses the selected unit per hour, with the difficult-terrain multiplier still applied. The daily/hourly choice does not alter a custom speed. Forced-march reminders still apply, so this mode describes a character's travel assumption, not a crewed vessel simulation.

## Outside the model

The planner does not model combat speed, climbing, swimming, encumbrance, weather, navigation failures, encounters, rest duration, magic, special mounts or mount relays. It does not calculate a wall-clock arrival date or enforce sleep requirements.

The old horse and gallop presets were undocumented fixed speeds. They are no longer offered as standard rules. The mounted-travel rules limit galloping duration and depend on access to fresh mounts; a constant custom speed does not reproduce those rules.

This version uses 2014 rules. It does not combine the 2014 and 2024 travel systems.
