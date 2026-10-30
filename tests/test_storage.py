import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from calculator_5e.core import Journey, Leg, ValidationError
from calculator_5e.storage import MAX_FILE_BYTES, load_route, loads_route, save_route


class StorageTests(unittest.TestCase):
    def test_round_trip_preserves_route(self):
        journey = Journey(
            (Leg("São Vicente", 12.5, "difficult"),),
            unit="km",
            pace="custom",
            custom_speed=3.6,
            hours_per_day=9.5,
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "route.json"
            save_route(path, journey)
            self.assertEqual(load_route(path), journey)

    def test_example_loads(self):
        self.assertEqual(len(load_route("examples/forest-road.json").legs), 3)

    def test_bom_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "route.json"
            path.write_text(json.dumps(Journey((Leg("Road", 1),)).to_dict()), encoding="utf-8-sig")
            self.assertEqual(load_route(path).legs[0].distance, 1)

    def test_invalid_shapes_and_fields(self):
        valid = Journey((Leg("Road", 1),)).to_dict()
        for data in (
            [],
            {},
            {**valid, "schema_version": 2},
            {**valid, "schema_version": True},
            {**valid, "hours": 6},
            {**valid, "legs": []},
            {**valid, "legs": [{}]},
            {**valid, "legs": [{"name": "Road", "distance": 1, "terain": "normal"}]},
            {**valid, "hours_per_day": "8"},
            {**valid, "hours_per_day": float("nan")},
        ):
            with self.subTest(data=data), self.assertRaises(ValidationError):
                loads_route(json.dumps(data))

    def test_duplicate_keys_and_malformed_json(self):
        for text in ('{"schema_version":1,"schema_version":2}', "{", "[" * 2000):
            with self.assertRaises(ValidationError):
                loads_route(text)

    def test_oversized_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.json"
            path.write_bytes(b" " * (MAX_FILE_BYTES + 1))
            with self.assertRaisesRegex(ValidationError, "128 KiB"):
                load_route(path)

    def test_failed_replace_keeps_previous_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "route.json"
            path.write_text("previous", encoding="utf-8")
            with patch("calculator_5e.storage.os.replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    save_route(path, Journey((Leg("Road", 1),)))
            self.assertEqual(path.read_text(encoding="utf-8"), "previous")
            self.assertEqual(list(Path(directory).iterdir()), [path])
