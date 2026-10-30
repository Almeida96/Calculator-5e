"""Pure travel calculations. Fractions keep day and save boundaries exact."""

import math
import unicodedata
from dataclasses import dataclass
from fractions import Fraction

MILES_TO_KM = Fraction("1.609344")
PACE_TABLE = {"slow": (2, 18), "normal": (3, 24), "fast": (4, 30)}
MAX_DAYS = 10_000
RULES_URL = "https://www.dndbeyond.com/sources/dnd/basic-rules-2014/adventuring#TravelPace"


class ValidationError(ValueError):
    """An input cannot be used to plan a journey."""


def number(value: object, field: str, *, maximum: float, positive: bool = False) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{field} must be a number.")
    try:
        valid = math.isfinite(value) and 0 <= value <= maximum
    except OverflowError:
        valid = False
    if not valid or (positive and value == 0):
        lower = "greater than 0" if positive else "at least 0"
        raise ValidationError(f"{field} must be finite, {lower}, and at most {maximum:g}.")
    return Fraction(str(value))


def choice(value: object, options: tuple | dict, field: str) -> None:
    if not isinstance(value, str) or value not in options:
        raise ValidationError(f"{field} must be one of: {', '.join(options)}.")


def fields(data: object, allowed: set[str], label: str) -> dict:
    if not isinstance(data, dict):
        raise ValidationError(f"{label} must be an object.")
    unknown = set(data) - allowed
    if unknown:
        raise ValidationError(f"Unknown {label} fields: {', '.join(sorted(map(str, unknown)))}.")
    return data


@dataclass(frozen=True)
class Leg:
    name: str
    distance: float
    terrain: str = "normal"

    def __post_init__(self) -> None:
        if (
            not isinstance(self.name, str)
            or not self.name.strip()
            or len(self.name) > 80
            or any(unicodedata.category(c) in ("Cc", "Cs") for c in self.name)
        ):
            raise ValidationError(
                "Leg name must contain 1–80 characters without control characters."
            )
        number(self.distance, "Distance", maximum=10_000_000)
        choice(self.terrain, ("normal", "difficult"), "Terrain")

    def to_dict(self) -> dict:
        return {"name": self.name, "distance": self.distance, "terrain": self.terrain}

    @classmethod
    def from_dict(cls, data: object) -> "Leg":
        data = fields(data, {"name", "distance", "terrain"}, "leg")
        if "name" not in data or "distance" not in data:
            raise ValidationError("Every leg needs a name and distance.")
        return cls(data["name"], data["distance"], data.get("terrain", "normal"))


@dataclass(frozen=True)
class Journey:
    legs: tuple[Leg, ...]
    unit: str = "mi"
    pace: str = "normal"
    hours_per_day: float = 8
    basis: str = "daily"
    custom_speed: float | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.legs, tuple)
            or not 1 <= len(self.legs) <= 100
            or any(not isinstance(leg, Leg) for leg in self.legs)
        ):
            raise ValidationError("A journey needs 1–100 legs.")
        choice(self.unit, ("mi", "km"), "Unit")
        choice(self.pace, (*PACE_TABLE, "custom"), "Pace")
        choice(self.basis, ("daily", "hourly"), "Calculation basis")
        number(self.hours_per_day, "Hours per day", maximum=24, positive=True)
        if self.pace == "custom":
            number(self.custom_speed, "Custom speed", maximum=10_000, positive=True)
        elif self.custom_speed is not None:
            raise ValidationError("Custom speed requires the custom pace.")

    def to_dict(self) -> dict:
        data = {
            "schema_version": 1,
            "unit": self.unit,
            "pace": self.pace,
            "hours_per_day": self.hours_per_day,
            "basis": self.basis,
            "legs": [leg.to_dict() for leg in self.legs],
        }
        if self.custom_speed is not None:
            data["custom_speed"] = self.custom_speed
        return data

    @classmethod
    def from_dict(cls, data: object) -> "Journey":
        data = fields(
            data,
            {"schema_version", "unit", "pace", "hours_per_day", "basis", "custom_speed", "legs"},
            "journey",
        )
        if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
            raise ValidationError("schema_version must be 1.")
        legs = data.get("legs")
        if not isinstance(legs, list) or not 1 <= len(legs) <= 100:
            raise ValidationError("A journey needs 1–100 legs.")
        options = {k: v for k, v in data.items() if k not in ("schema_version", "legs")}
        return cls(tuple(Leg.from_dict(leg) for leg in legs), **options)


def rounded(value: Fraction) -> float:
    return round(float(value), 6)


def rules() -> dict:
    return {
        "edition": "D&D 2014 / SRD 5.1",
        "source": RULES_URL,
        "pace_table": {
            p: {"miles_per_hour": h, "miles_per_day": d} for p, (h, d) in PACE_TABLE.items()
        },
        "standard_day_hours": 8,
        "difficult_terrain_multiplier": 0.5,
        "daily_basis": "Interpolate the daily distance over the first 8 hours; use the hourly "
        "column after that. Partial days are a planning approximation.",
        "hourly_basis": "Use the hourly column for all movement; 8-hour totals differ from "
        "the daily table for slow and fast paces.",
        "forced_march": "One Constitution save after each completed travel hour beyond 8, "
        "DC 10 + hours beyond 8. Saves and exhaustion effects are not simulated.",
        "mounts": "Mount relays and galloping limits are not modeled. "
        "Custom speed is a house rule.",
    }


def plan(journey: Journey, *, max_days: int = MAX_DAYS) -> dict:
    """Allocate consecutive legs to travel days without resetting time at leg boundaries."""
    if not isinstance(journey, Journey):
        raise ValidationError("Expected a Journey.")
    if type(max_days) is not int or not 1 <= max_days <= MAX_DAYS:
        raise ValidationError(f"Day limit must be an integer from 1 to {MAX_DAYS:,}.")
    budget = Fraction(str(journey.hours_per_day))
    unit_factor = MILES_TO_KM if journey.unit == "km" else Fraction(1)
    if journey.pace == "custom":
        base = overtime = Fraction(str(journey.custom_speed))
        assumption = "Custom speed in the selected unit per hour; terrain still applies."
    else:
        hourly, daily = PACE_TABLE[journey.pace]
        base = (Fraction(daily, 8) if journey.basis == "daily" else Fraction(hourly)) * unit_factor
        overtime = Fraction(hourly) * unit_factor
        assumption = rules()[journey.basis + "_basis"]
    capacity = base * min(budget, 8) + overtime * max(budget - 8, 0)
    effort = sum(
        (
            Fraction(str(leg.distance)) * (2 if leg.terrain == "difficult" else 1)
            for leg in journey.legs
        ),
        Fraction(0),
    )
    if effort > capacity * max_days:
        raise ValidationError(f"Journey exceeds {max_days:,} travel days; shorten the route.")
    days = []
    day_hours = Fraction(0)
    day_distance = Fraction(0)
    total_hours = Fraction(0)
    segments = []

    def finish_day() -> None:
        days.append(
            {
                "day": len(days) + 1,
                "distance": rounded(day_distance),
                "moving_hours": rounded(day_hours),
                "segments": list(segments),
                "forced_march_saves": [
                    {"after_hour": hour, "dc": 10 + hour - 8}
                    for hour in range(9, math.floor(day_hours) + 1)
                ],
            }
        )

    for index, leg in enumerate(journey.legs):
        remaining = Fraction(str(leg.distance))
        terrain = Fraction(1, 2) if leg.terrain == "difficult" else Fraction(1)
        while remaining:
            phase_end = min(budget, Fraction(8)) if day_hours < 8 else budget
            speed = (base if day_hours < 8 else overtime) * terrain
            hours = min(remaining / speed, phase_end - day_hours)
            distance = hours * speed
            segments.append(
                {
                    "leg": index + 1,
                    "name": leg.name,
                    "terrain": leg.terrain,
                    "distance": rounded(distance),
                    "moving_hours": rounded(hours),
                }
            )
            remaining -= distance
            day_hours += hours
            total_hours += hours
            day_distance += distance
            if day_hours == budget:
                finish_day()
                day_hours = day_distance = Fraction(0)
                segments = []
    if day_hours:
        finish_day()
    notes = [
        assumption,
        "Travel days exclude rest-only days, encounters and other delays.",
        "Constitution saves are listed only after completed hours beyond 8; exhaustion "
        "and its movement effects are not applied.",
    ]
    if journey.pace == "fast":
        notes.append("Fast pace: -5 to passive Wisdom (Perception).")
    if journey.pace == "slow":
        notes.append("Slow pace permits stealth; other conditions still apply.")
    return {
        "schema_version": 1,
        "ruleset": rules()["edition"],
        "rules_source": RULES_URL,
        "unit": journey.unit,
        "pace": journey.pace,
        "basis": journey.basis,
        "hours_per_day": journey.hours_per_day,
        "custom_speed": journey.custom_speed,
        "total_distance": rounded(
            sum((Fraction(str(x.distance)) for x in journey.legs), Fraction(0))
        ),
        "moving_hours": rounded(total_hours),
        "travel_days": len(days),
        "last_day_hours": days[-1]["moving_hours"] if days else 0,
        "notes": notes,
        "days": days,
    }
