import json
import subprocess
import sys
import unittest


def run(*args):
    return subprocess.run(
        [sys.executable, "-m", "calculator_5e", *args], text=True, capture_output=True, timeout=15
    )


class CliTests(unittest.TestCase):
    def test_json_output_is_machine_readable(self):
        result = run("trip", "38", "--pace", "fast", "--hours", "10", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output["moving_hours"], 10)
        self.assertEqual(result.stderr, "")

    def test_route_command(self):
        result = run("route", "examples/forest-road.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Travel days: 2", result.stdout)
        self.assertIn("Forest trail: 6 mi", result.stdout)

    def test_validation_errors_do_not_emit_partial_results(self):
        for arguments in (
            ("trip", "1", "--hours", "0"),
            ("trip", "-1"),
            ("trip", "nan"),
            ("route", "missing.json"),
            ("trip", "1", "--speed", "2"),
        ):
            with self.subTest(arguments=arguments):
                result = run(*arguments)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn("Error:", result.stderr)

    def test_rules_are_available_without_gui(self):
        result = run("rules")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["pace_table"]["fast"]["miles_per_day"], 30)

    def test_import_does_not_launch_gui(self):
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import main; import tkinter; assert tkinter._default_root is None",
            ],
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
