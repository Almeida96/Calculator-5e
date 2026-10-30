import unittest
from dataclasses import replace

from calculator_5e.core import Journey, Leg, ValidationError, plan


def trip(distance=24, **options):
    return Journey((Leg("Road", distance),), **options)


class TravelTests(unittest.TestCase):
    def test_daily_table(self):
        for pace, distance in [("slow", 18), ("normal", 24), ("fast", 30)]:
            with self.subTest(pace=pace):
                result = plan(trip(distance, pace=pace))
                self.assertEqual((result["travel_days"], result["moving_hours"]), (1, 8))
                self.assertEqual(result["days"][0]["forced_march_saves"], [])

    def test_hourly_table(self):
        for pace, distance in [("slow", 16), ("normal", 24), ("fast", 32)]:
            with self.subTest(pace=pace):
                self.assertEqual(plan(trip(distance, pace=pace, basis="hourly"))["moving_hours"], 8)

    def test_partial_day_interpolation_is_explicit(self):
        result = plan(trip(15, pace="fast", hours_per_day=4))
        self.assertEqual((result["travel_days"], result["moving_hours"]), (1, 4))
        self.assertIn("approximation", result["notes"][0])

    def test_difficult_terrain_halves_speed(self):
        result = plan(Journey((Leg("Forest", 24, "difficult"),)))
        self.assertEqual((result["travel_days"], result["moving_hours"]), (2, 16))
        self.assertEqual([day["distance"] for day in result["days"]], [12, 12])

    def test_mixed_route_carries_time_across_legs_and_days(self):
        result = plan(Journey((Leg("Road", 12), Leg("Forest", 9, "difficult"), Leg("Keep", 6))))
        self.assertEqual(result["moving_hours"], 12)
        self.assertEqual([day["distance"] for day in result["days"]], [18, 9])
        self.assertEqual(result["last_day_hours"], 4)
        self.assertEqual(result["days"][1]["segments"][0]["distance"], 3)

    def test_miles_and_kilometers_describe_same_journey(self):
        miles = plan(trip(48))
        km = plan(trip(77.248512, unit="km"))
        self.assertEqual(km["moving_hours"], miles["moving_hours"])
        self.assertEqual(km["travel_days"], 2)

    def test_forced_march_uses_hourly_column_after_eight_hours(self):
        result = plan(trip(38, pace="fast", hours_per_day=10))
        self.assertEqual(result["moving_hours"], 10)
        self.assertEqual(result["travel_days"], 1)
        self.assertEqual(
            result["days"][0]["forced_march_saves"],
            [{"after_hour": 9, "dc": 11}, {"after_hour": 10, "dc": 12}],
        )

    def test_slow_forced_march_uses_two_miles_per_extra_hour(self):
        self.assertEqual(plan(trip(22, pace="slow", hours_per_day=10))["moving_hours"], 10)

    def test_forced_march_resets_each_day(self):
        result = plan(trip(60, hours_per_day=10))
        self.assertEqual(len(result["days"]), 2)
        self.assertEqual(
            result["days"][0]["forced_march_saves"], result["days"][1]["forced_march_saves"]
        )

    def test_save_boundaries_are_not_rounded_up(self):
        for distance, expected in [(24, 0), (26.999999, 0), (27, 1), (28.5, 1), (30, 2)]:
            with self.subTest(distance=distance):
                result = plan(trip(distance, hours_per_day=10))
                self.assertEqual(len(result["days"][0]["forced_march_saves"]), expected)

    def test_no_phantom_day_at_decimal_boundary(self):
        result = plan(
            Journey(
                tuple(Leg(f"Leg {i}", 0.1) for i in range(30)),
                pace="custom",
                custom_speed=0.3,
                hours_per_day=10,
            )
        )
        self.assertEqual((result["travel_days"], result["moving_hours"]), (1, 10))

    def test_zero_distance_and_zero_legs_inside_route(self):
        self.assertEqual(plan(trip(0))["travel_days"], 0)
        self.assertEqual(plan(trip(0))["moving_hours"], 0)
        result = plan(Journey((Leg("Start", 0), Leg("Road", 24), Leg("End", 0))))
        self.assertEqual(result["travel_days"], 1)

    def test_custom_speed_and_terrain(self):
        result = plan(
            Journey((Leg("Trail", 36, "difficult"),), unit="km", pace="custom", custom_speed=3.6)
        )
        self.assertEqual((result["travel_days"], result["moving_hours"]), (3, 20))
        self.assertIn("Custom", result["notes"][0])

    def test_day_limit_rejects_unbounded_work(self):
        with self.assertRaisesRegex(ValidationError, "10,000"):
            plan(trip(10_000_000, hours_per_day=0.001))

    def test_day_limit_accounts_for_terrain_and_overtime(self):
        self.assertEqual(
            plan(trip(38, pace="fast", hours_per_day=10), max_days=1)["travel_days"], 1
        )
        with self.assertRaises(ValidationError):
            plan(Journey((Leg("Forest", 24, "difficult"),)), max_days=1)

    def test_unpaired_surrogates_and_control_characters_are_rejected(self):
        for name in ("bad\ud800", "bad\u0085"):
            with self.assertRaises(ValidationError):
                Leg(name, 1)

    def test_split_route_has_same_total_as_combined_route(self):
        for pace in ("slow", "normal", "fast"):
            for hours in (4, 8, 10, 24):
                for basis in ("daily", "hourly"):
                    options = dict(pace=pace, hours_per_day=hours, basis=basis)
                    combined = plan(trip(72, **options))
                    split = plan(Journey(tuple(Leg(str(i), 9) for i in range(8)), **options))
                    self.assertEqual(split["moving_hours"], combined["moving_hours"])
                    self.assertEqual(split["travel_days"], combined["travel_days"])

    def test_distance_and_time_are_conserved(self):
        route = Journey(
            (Leg("Road", 32.5), Leg("Marsh", 19.25, "difficult"), Leg("Hill", 4.75)),
            pace="fast",
            hours_per_day=10,
        )
        result = plan(route)
        self.assertAlmostEqual(sum(d["distance"] for d in result["days"]), 56.5, places=5)
        self.assertAlmostEqual(
            sum(d["moving_hours"] for d in result["days"]), result["moving_hours"], places=5
        )

    def test_invalid_numbers(self):
        for value in (-1, float("nan"), float("inf"), True, "3", None, 10**1000):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(ValidationError):
                    Leg("Road", value)
                with self.assertRaises(ValidationError):
                    trip(hours_per_day=value)
        for hours in (0, 24.01):
            with self.assertRaises(ValidationError):
                trip(hours_per_day=hours)

    def test_invalid_options(self):
        for options in (
            {"pace": "gallop"},
            {"unit": "feet"},
            {"basis": "2024"},
            {"custom_speed": 3},
            {"pace": "custom"},
            {"pace": "custom", "custom_speed": 0},
        ):
            with self.subTest(options=options), self.assertRaises(ValidationError):
                trip(**options)
        for name in ("", " ", "x" * 81, "line\nbreak"):
            with self.assertRaises(ValidationError):
                Leg(name, 1)
        with self.assertRaises(ValidationError):
            Leg("Road", 1, "unknown")
        with self.assertRaises(ValidationError):
            Journey(())
        with self.assertRaises(ValidationError):
            replace(trip(), legs=(Leg("Road", 1),) * 101)
