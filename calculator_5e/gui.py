"""Tkinter route editor. Importing this module never creates a window."""

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .cli import format_plan
from .core import MILES_TO_KM, Journey, Leg, ValidationError, plan
from .storage import load_route, save_route


class TravelApp(ttk.Frame):
    def __init__(self, root: tk.Tk):
        super().__init__(root, padding=16)
        self.root = root
        self.pack(fill="both", expand=True)
        root.title("Calculator 5e — Travel planner")
        root.geometry("1000x780")
        root.minsize(820, 650)
        self.legs: list[Leg] = []
        self.result: dict | None = None
        self.dirty = False
        self.previous_unit = "mi"
        self.unit = tk.StringVar(value="mi")
        self.pace = tk.StringVar(value="normal")
        self.basis = tk.StringVar(value="daily")
        self.hours = tk.StringVar(value="8")
        self.speed = tk.StringVar()
        self.name = tk.StringVar(value="Road to the forest")
        self.distance = tk.StringVar(value="12")
        self.terrain = tk.StringVar(value="normal")
        self.status = tk.StringVar(value="Add the legs of your journey, then calculate.")
        self._build()
        for variable in (self.pace, self.basis, self.hours, self.speed):
            variable.trace_add("write", self._settings_changed)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.bind("<Control-s>", lambda _event: self.save())
        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)

    def _build(self) -> None:
        heading = ttk.Frame(self)
        heading.grid(row=0, column=0, sticky="ew")
        ttk.Label(heading, text="Overland travel", font=("", 20, "bold")).pack(side="left")
        ttk.Button(heading, text="Open route…", command=self.open).pack(side="right")
        ttk.Button(heading, text="Save route…", command=self.save).pack(side="right", padx=6)
        settings = ttk.LabelFrame(self, text="Journey settings · D&D 2014", padding=10)
        settings.grid(row=1, column=0, sticky="ew", pady=12)
        for column, (label, variable, values) in enumerate(
            [
                ("Distance unit", self.unit, ("mi", "km")),
                ("Pace", self.pace, ("slow", "normal", "fast", "custom")),
                ("Calculation basis", self.basis, ("daily", "hourly")),
            ]
        ):
            ttk.Label(settings, text=label).grid(row=0, column=column, sticky="w")
            control = ttk.Combobox(
                settings, textvariable=variable, values=values, state="readonly", width=17
            )
            control.grid(row=1, column=column, padx=(0, 12), sticky="ew")
            if variable is self.unit:
                control.bind("<<ComboboxSelected>>", self.convert_units)
        ttk.Label(settings, text="Hours / day").grid(row=0, column=3, sticky="w")
        ttk.Entry(settings, textvariable=self.hours, width=12).grid(row=1, column=3, padx=(0, 12))
        ttk.Label(settings, text="Custom speed / hour").grid(row=0, column=4, sticky="w")
        self.speed_entry = ttk.Entry(settings, textvariable=self.speed, width=18, state="disabled")
        self.speed_entry.grid(row=1, column=4)
        ttk.Label(
            settings,
            text="Daily: interpolate the 8-hour daily total. "
            "Hourly: use the hourly table. Terrain applies to both.",
            wraplength=860,
        ).grid(row=2, column=0, columnspan=5, sticky="w", pady=(10, 0))

        editor = ttk.LabelFrame(self, text="Route legs", padding=10)
        editor.grid(row=2, column=0, sticky="ew")
        editor.columnconfigure(0, weight=1)
        for column, label in enumerate(("Name", "Distance", "Terrain")):
            ttk.Label(editor, text=label).grid(row=0, column=column, sticky="w")
        ttk.Entry(editor, textvariable=self.name).grid(row=1, column=0, sticky="ew", padx=(0, 10))
        ttk.Entry(editor, textvariable=self.distance, width=14).grid(row=1, column=1, padx=(0, 10))
        ttk.Combobox(
            editor,
            textvariable=self.terrain,
            values=("normal", "difficult"),
            width=14,
            state="readonly",
        ).grid(row=1, column=2, padx=(0, 10))
        ttk.Button(editor, text="Add leg", command=self.add_leg).grid(row=1, column=3)
        ttk.Button(editor, text="Update selected", command=self.update_leg).grid(row=1, column=4)
        self.tree = ttk.Treeview(
            editor,
            columns=("name", "distance", "terrain"),
            show="headings",
            selectmode="browse",
            height=5,
        )
        for key, width in (("name", 420), ("distance", 100), ("terrain", 130)):
            self.tree.heading(key, text=key.title())
            self.tree.column(key, width=width, minwidth=70, stretch=key == "name")
        self.tree.grid(row=2, column=0, columnspan=5, sticky="ew", pady=10)
        scrollbar = ttk.Scrollbar(editor, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=2, column=5, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.select_leg)
        buttons = ttk.Frame(editor)
        buttons.grid(row=3, column=0, columnspan=5, sticky="w")
        for label, command in (
            ("Remove", self.remove_leg),
            ("Move up", lambda: self.move_leg(-1)),
            ("Move down", lambda: self.move_leg(1)),
        ):
            ttk.Button(buttons, text=label, command=command).pack(side="left", padx=(0, 6))
        actions = ttk.Frame(self)
        actions.grid(row=3, column=0, sticky="ew", pady=12)
        ttk.Button(actions, text="Calculate journey", command=self.calculate).pack(side="left")
        self.copy_button = ttk.Button(
            actions, text="Copy itinerary", command=self.copy, state="disabled"
        )
        self.copy_button.pack(side="left", padx=8)
        self.export_button = ttk.Button(
            actions, text="Export results…", command=self.export, state="disabled"
        )
        self.export_button.pack(side="left")
        ttk.Label(self, textvariable=self.status, wraplength=900).grid(
            row=4, column=0, sticky="w", pady=(0, 6)
        )
        output = ttk.Frame(self)
        output.grid(row=5, column=0, sticky="nsew")
        output.columnconfigure(0, weight=1)
        output.rowconfigure(0, weight=1)
        self.output = tk.Text(output, wrap="word", height=12, state="disabled", padx=10, pady=10)
        self.output.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(output, orient="vertical", command=self.output.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.output.configure(yscrollcommand=scroll.set)

    def _write_output(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", text)
        self.output.configure(state="disabled")

    def changed(self) -> None:
        self.dirty = True
        self.result = None
        self._write_output("")
        self.copy_button.configure(state="disabled")
        self.export_button.configure(state="disabled")
        self.status.set("Route changed. Calculate to refresh the itinerary.")

    def _settings_changed(self, *_args) -> None:
        self.speed_entry.configure(state="normal" if self.pace.get() == "custom" else "disabled")
        self.changed()

    def selected(self) -> int | None:
        selection = self.tree.selection()
        return int(selection[0]) if selection else None

    def refresh(self, selection: int | None = None) -> None:
        self.tree.delete(*self.tree.get_children())
        self.tree.heading("distance", text=f"Distance ({self.unit.get()})")
        for index, leg in enumerate(self.legs):
            self.tree.insert(
                "", "end", iid=str(index), values=(leg.name, f"{leg.distance:g}", leg.terrain)
            )
        if selection is not None and selection < len(self.legs):
            self.tree.selection_set(str(selection))

    def read_leg(self) -> Leg:
        return Leg(self.name.get().strip(), float(self.distance.get()), self.terrain.get())

    def add_leg(self) -> None:
        try:
            if len(self.legs) >= 100:
                raise ValidationError("A journey supports at most 100 legs.")
            leg = self.read_leg()
            self.legs.append(leg)
            self.changed()
            self.refresh(len(self.legs) - 1)
        except ValueError as exc:
            self.status.set(f"Cannot add leg: {exc}")

    def update_leg(self) -> None:
        index = self.selected()
        if index is None:
            self.status.set("Select a leg to update.")
            return
        try:
            self.legs[index] = self.read_leg()
            self.changed()
            self.refresh(index)
        except ValueError as exc:
            self.status.set(f"Cannot update leg: {exc}")

    def select_leg(self, _event=None) -> None:
        index = self.selected()
        if index is not None:
            leg = self.legs[index]
            self.name.set(leg.name)
            self.distance.set(str(leg.distance))
            self.terrain.set(leg.terrain)

    def remove_leg(self) -> None:
        index = self.selected()
        if index is not None:
            self.legs.pop(index)
            self.changed()
            self.refresh(min(index, len(self.legs) - 1) if self.legs else None)

    def move_leg(self, offset: int) -> None:
        index = self.selected()
        if index is not None and 0 <= index + offset < len(self.legs):
            self.legs[index], self.legs[index + offset] = (
                self.legs[index + offset],
                self.legs[index],
            )
            self.changed()
            self.refresh(index + offset)

    def convert_units(self, _event=None) -> None:
        unit = self.unit.get()
        if unit == self.previous_unit:
            return
        factor = float(MILES_TO_KM) if unit == "km" else 1 / float(MILES_TO_KM)
        try:
            converted = [
                Leg(leg.name, round(leg.distance * factor, 12), leg.terrain) for leg in self.legs
            ]
            pending_distance = str(round(float(self.distance.get()) * factor, 12))
            speed = str(round(float(self.speed.get()) * factor, 12)) if self.speed.get() else ""
            # Validate the custom speed before changing any route data.
            if self.pace.get() == "custom":
                Journey(
                    tuple(converted) or (Leg("Check", 0),),
                    unit=unit,
                    pace="custom",
                    custom_speed=float(speed),
                )
        except ValueError as exc:
            self.unit.set(self.previous_unit)
            self.status.set(f"Cannot convert units: {exc}")
            return
        self.legs = converted
        self.distance.set(pending_distance)
        self.speed.set(speed)
        self.previous_unit = unit
        self.changed()
        self.refresh()
        self.status.set(f"Distances and custom speed converted to {unit}.")

    def journey(self) -> Journey:
        return Journey(
            tuple(self.legs),
            self.unit.get(),
            self.pace.get(),
            float(self.hours.get()),
            self.basis.get(),
            float(self.speed.get()) if self.pace.get() == "custom" else None,
        )

    def calculate(self) -> None:
        try:
            self.result = plan(self.journey())
            self._write_output(format_plan(self.result))
            self.copy_button.configure(state="normal")
            self.export_button.configure(state="normal")
            self.status.set(
                f"{self.result['travel_days']} travel days · "
                f"{self.result['moving_hours']:g} moving hours"
            )
        except ValueError as exc:
            self.result = None
            self._write_output("")
            self.copy_button.configure(state="disabled")
            self.export_button.configure(state="disabled")
            self.status.set(f"Cannot calculate: {exc}")

    def discard_changes(self) -> bool:
        return not self.dirty or messagebox.askyesno(
            "Unsaved route", "Discard unsaved changes?", parent=self.root
        )

    def open(self) -> None:
        if not self.discard_changes():
            return
        path = filedialog.askopenfilename(filetypes=[("Route JSON", "*.json")], parent=self.root)
        if not path:
            return
        try:
            journey = load_route(path)
        except (OSError, ValueError) as exc:
            self.status.set(f"Cannot open route: {exc}")
            return
        self.legs = list(journey.legs)
        self.unit.set(journey.unit)
        self.previous_unit = journey.unit
        self.pace.set(journey.pace)
        self.basis.set(journey.basis)
        self.hours.set(str(journey.hours_per_day))
        self.speed.set("" if journey.custom_speed is None else str(journey.custom_speed))
        self.refresh(0)
        self.dirty = False
        self.calculate()

    def save(self) -> None:
        try:
            journey = self.journey()
            path = filedialog.asksaveasfilename(
                defaultextension=".json", filetypes=[("Route JSON", "*.json")], parent=self.root
            )
            if path:
                save_route(path, journey)
                self.dirty = False
                self.status.set(f"Saved route: {Path(path).name}")
        except (OSError, ValueError) as exc:
            self.status.set(f"Cannot save route: {exc}")

    def copy(self) -> None:
        if self.result is not None:
            self.root.clipboard_clear()
            self.root.clipboard_append(format_plan(self.result))
            self.status.set("Itinerary copied.")

    def export(self) -> None:
        if self.result is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("Result JSON", "*.json")], parent=self.root
        )
        if path:
            try:
                Path(path).write_text(
                    json.dumps(self.result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
                )
                self.status.set(f"Exported results: {Path(path).name}")
            except OSError as exc:
                self.status.set(f"Cannot export results: {exc}")

    def close(self) -> None:
        if self.discard_changes():
            self.root.destroy()


def main() -> None:
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise RuntimeError(
            "Tk could not open a display. Use the CLI, or install Tk and run in a desktop session."
        ) from exc
    TravelApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
