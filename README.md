# Calculator 5e

Plan an overland journey for a D&D 2014 game. Build a route with roads and difficult terrain, choose a travel pace, and get an itinerary with daily distances and forced-march saving throws.

The desktop app, command line and optional MCP server share the same calculation engine. The desktop app and CLI use only the Python standard library.

## Run it

Requires Python 3.11 or newer. Clone this repository, then run:

```sh
python main.py
```

The desktop app needs Tkinter and a graphical desktop. On Debian/Ubuntu, install `python3-tk` if it is missing. Windows Python installers normally include Tcl/Tk; minimal Python distributions may omit it.

For a terminal-only session:

```sh
python -m calculator_5e route examples/forest-road.json
```

The included route has 12 miles of road, 9 miles of difficult forest and another 6 miles of road. At normal pace with eight travel hours per day:

```text
27 mi | normal | daily basis
Travel days: 2
Moving time: 12 hours
Final day: 4 hours

Day 1: 18 mi, 8 hours
  Road to the forest: 12 mi (normal)
  Forest trail: 6 mi (difficult)
Day 2: 9 mi, 4 hours
  Forest trail: 3 mi (difficult)
  Road to the keep: 6 mi (normal)
```

The command also prints the calculation assumptions after the itinerary.

## Plan a route

- Add, edit, remove and reorder up to 100 route legs.
- Switch between miles and kilometers; the desktop app converts existing distances.
- Choose slow, normal or fast pace, or enter a custom speed for a house rule.
- Set travel hours per day and see Constitution save DCs for completed hours beyond eight.
- Save and reopen route files; copy the itinerary or export the results as JSON.

A single-leg calculation is also available:

```sh
python -m calculator_5e trip 38 --pace fast --hours 10
python -m calculator_5e trip 60 --unit km --terrain difficult --json
python -m calculator_5e rules
```

To install the commands in a virtual environment:

```sh
python -m venv .venv
# Activate the environment using the command for your shell.
python -m pip install .
calculator-5e route examples/forest-road.json
calculator-5e-gui
```

Activation commands and the full CLI reference are in the [user guide](docs/usage.md).

## Which rules does it use?

The [2014 travel rules](https://www.dndbeyond.com/sources/dnd/basic-rules-2014/adventuring#TravelPace), also in SRD 5.1. This is an overland planner, not a combat movement calculator.

The hourly and daily pace tables do not scale identically: fast pace is 4 miles per hour but 30 miles per day. The default **daily** basis spreads the daily total across the first eight hours, then uses the hourly rate for extra hours. **Hourly** basis uses the hourly rate throughout. Partial-day interpolation is a planning convention, not an additional official rule.

Results include the selected basis. Exhaustion, encounters, weather, rests and mount relays require a DM's judgment. See [rules and assumptions](docs/rules.md) for examples and exclusions.

## Use with an agent

Install the optional MCP dependencies:

```sh
python -m pip install ".[mcp]"
python -m calculator_5e mcp
```

This starts a local stdio server for an MCP client. It provides `plan_journey`, `compare_paces` and `travel_rules`, with structured inputs and results. An agent can use these tools to calculate a journey and explain the result. The server does not call a model, read campaign files or require an API key.

See the [MCP setup and example conversation](docs/mcp.md). Its integration test connects a real SDK client to a server subprocess; it does not require a live model provider.

## Development

```sh
python -m pip install -e ".[mcp,dev]"
python -m unittest discover -s tests -v
python -m ruff check .
python -m ruff format --check .
python -m build
python tools/smoke_package.py
```

GitHub Actions runs tests on Windows and Linux with Python 3.11 and 3.14, checks formatting, and builds and smoke-tests the wheel. GUI tests run against Tk, using Xvfb on Linux. Local GUI tests skip if no display is available; set `CALCULATOR_REQUIRE_GUI_TESTS=1` to require them.

- [Architecture and calculation flow](docs/architecture.md)
- [Contribution guide](CONTRIBUTING.md)
- [Changes from the original calculator](CHANGELOG.md)
- [SRD attribution](NOTICE.md)

No license for the application source has been declared. The SRD material has its own license, described in the attribution notice.
