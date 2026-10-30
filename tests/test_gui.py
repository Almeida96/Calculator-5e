import os
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from calculator_5e.core import Journey, Leg
from calculator_5e.gui import TravelApp
from calculator_5e.storage import save_route


class GuiTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
            self.root.withdraw()
        except tk.TclError as exc:
            if os.environ.get("CALCULATOR_REQUIRE_GUI_TESTS") == "1":
                raise
            self.skipTest(f"Tk display unavailable: {exc}")
        self.app = TravelApp(self.root)
        self.root.update_idletasks()

    def tearDown(self):
        if hasattr(self, "root"):
            self.root.destroy()

    def add(self, name, distance, terrain="normal"):
        self.app.name.set(name)
        self.app.distance.set(str(distance))
        self.app.terrain.set(terrain)
        self.app.add_leg()

    def test_route_editing_and_calculation(self):
        self.add("Road", 12)
        self.add("Forest", 9, "difficult")
        self.add("Keep", 6)
        self.app.calculate()
        self.assertEqual(self.app.result["moving_hours"], 12)
        self.app.tree.selection_set("2")
        self.app.move_leg(-1)
        self.assertEqual([leg.name for leg in self.app.legs], ["Road", "Keep", "Forest"])
        self.app.remove_leg()
        self.assertEqual(len(self.app.legs), 2)
        self.assertIsNone(self.app.result)

    def test_invalid_update_preserves_leg(self):
        self.add("Road", 24)
        self.app.tree.selection_set("0")
        self.app.distance.set("-5")
        self.app.update_leg()
        self.assertEqual(self.app.legs[0].distance, 24)
        self.assertIn("Cannot update", self.app.status.get())

    def test_invalid_hours_clear_stale_results(self):
        self.add("Road", 24)
        self.app.calculate()
        self.assertIsNotNone(self.app.result)
        self.app.hours.set("0")
        self.assertIsNone(self.app.result)
        self.app.calculate()
        self.assertIn("Cannot calculate", self.app.status.get())
        self.assertEqual(str(self.app.export_button["state"]), "disabled")

    def test_unit_switch_converts_existing_route(self):
        self.add("Road", 24)
        self.app.unit.set("km")
        self.app.convert_units()
        self.app.calculate()
        self.assertEqual(self.app.legs[0].distance, 38.624256)
        self.assertEqual(self.app.result["moving_hours"], 8)
        self.app.unit.set("mi")
        self.app.convert_units()
        self.assertEqual(self.app.legs[0].distance, 24)

    def test_open_valid_route_and_reject_invalid_without_losing_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "route.json"
            save_route(path, Journey((Leg("Forest", 9, "difficult"),), hours_per_day=6))
            with patch("calculator_5e.gui.filedialog.askopenfilename", return_value=str(path)):
                self.app.open()
                self.assertEqual(self.app.result["moving_hours"], 6)
                self.assertFalse(self.app.dirty)
                path.write_text("invalid", encoding="utf-8")
                self.app.open()
                self.assertEqual(self.app.legs[0].name, "Forest")
                self.assertIn("Cannot open", self.app.status.get())

    def test_cancel_discard_keeps_current_route(self):
        self.add("Road", 24)
        with patch("calculator_5e.gui.messagebox.askyesno", return_value=False):
            with patch("calculator_5e.gui.filedialog.askopenfilename") as picker:
                self.app.open()
                picker.assert_not_called()
        self.assertEqual(len(self.app.legs), 1)
