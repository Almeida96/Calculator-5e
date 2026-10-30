# User guide

## Desktop

Run `python main.py` from the repository, or install the package and run `calculator-5e-gui`.

1. Choose the unit, pace, calculation basis and travel hours per day.
2. Enter a leg name, distance and terrain, then select **Add leg**.
3. Repeat for the rest of the route.
4. Select **Calculate journey** to see the itinerary.

Select a row to load it into the editor. **Update selected** applies edits to that row; **Add leg** appends another row. Use **Move up**, **Move down** or **Remove** to change the sequence.

Changing journey settings or the saved leg list clears the old itinerary. Changing the editor fields takes effect when you add or update a leg. **Custom** pace enables the speed field; its unit is miles/hour or kilometers/hour, matching the distance unit. Switching units converts the existing route and custom speed.

**Save route** stores the inputs, including terrain and settings. **Export results** stores the calculated itinerary. These are different file formats: reopen a saved route to edit it; use a result file for reports or other tools. The app asks before discarding unsaved route changes.

## Installation

Use a virtual environment to keep optional MCP and development dependencies separate.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\calculator-5e.exe trip 24
.\.venv\Scripts\calculator-5e-gui.exe
```

Linux/macOS:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
calculator-5e trip 24
calculator-5e-gui
```

You can also activate the Windows environment with `.\.venv\Scripts\Activate.ps1` if your PowerShell policy permits it. Activation is optional when you use the executable's full path.

The package is installed from this checkout; these commands do not assume a PyPI release.

## CLI

```text
calculator-5e trip DISTANCE [--unit mi|km]
    [--pace slow|normal|fast|custom] [--hours HOURS]
    [--basis daily|hourly] [--terrain normal|difficult]
    [--speed CUSTOM_SPEED] [--json]

calculator-5e route PATH [--json]
calculator-5e rules
calculator-5e gui
calculator-5e mcp
```

Defaults are miles, normal pace, eight hours per day, normal terrain and daily basis. `--speed` requires `--pace custom`. For example, the original calculator's walking-speed assumption can be entered explicitly:

```sh
python -m calculator_5e trip 36 --unit km --pace custom --speed 3.6
```

Normal output is readable text. `--json` emits one JSON object on stdout. Errors go to stderr and exit with status 2; successful commands exit with status 0. No result is printed for invalid input. Use `--help` on a command for its arguments.

## Route format

See [forest-road.json](../examples/forest-road.json) and the [JSON Schema](../schemas/route.schema.json).

```json
{
  "schema_version": 1,
  "unit": "mi",
  "pace": "normal",
  "hours_per_day": 8,
  "basis": "daily",
  "legs": [
    {"name": "North road", "distance": 12, "terrain": "normal"},
    {"name": "Marsh", "distance": 6, "terrain": "difficult"}
  ]
}
```

Only `schema_version` and `legs` are required at the top level. Each leg needs a name and distance. Other settings use the defaults above. A custom pace also needs `custom_speed`.

Files use UTF-8; a UTF-8 BOM is accepted. Unknown fields, duplicate JSON keys, nonfinite numbers and numeric strings are rejected. Routes support 1–100 legs, names of 1–80 characters without control characters, distances from 0 to 10,000,000 in the selected unit, and travel hours greater than 0 and at most 24. Custom speed must be greater than 0 and at most 10,000. Calculations stop with an error beyond 10,000 travel days. The file limit is 128 KiB.

Zero-length legs are allowed. An entirely zero-length route has zero travel days and no saves.

## Result format

JSON results include the input unit, pace and basis, total distance, moving hours, travel-day count, final-day hours, explanatory notes and the source of the rules. Each day contains route segments and a list of saves with `after_hour` and `dc`.

A segment references its leg by a one-based index. One leg may span several days, or appear twice on a day when the calculation crosses the eight-hour rate boundary. Output numbers are rounded to six decimal places; totals are calculated before rounding.

## Troubleshooting

**Tkinter missing:** install your Python distribution's Tcl/Tk component. On Debian/Ubuntu this is usually `sudo apt install python3-tk`. The CLI does not need Tkinter.

**No display:** use the CLI on headless machines. Linux GUI tests use `xvfb-run -a python -m unittest discover -s tests -v`.

**MCP dependency missing:** install `".[mcp]"` using the same Python interpreter configured in your client.

**Different result from the old app:** the defaults now follow the 2014 pace table. Use custom speed for the old assumptions; see the [migration notes](../CHANGELOG.md).
