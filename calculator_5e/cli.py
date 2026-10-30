"""Command line interface; calculation output goes to stdout, errors to stderr."""

import argparse
import json
import sys

from . import __version__
from .core import Journey, Leg, ValidationError, plan, rules
from .storage import load_route


def format_plan(result: dict) -> str:
    unit = result["unit"]
    lines = [
        f"{result['total_distance']:g} {unit} | {result['pace']} | {result['basis']} basis",
        f"Travel days: {result['travel_days']}",
        f"Moving time: {result['moving_hours']:g} hours",
        f"Final day: {result['last_day_hours']:g} hours",
        "",
    ]
    for day in result["days"]:
        lines.append(f"Day {day['day']}: {day['distance']:g} {unit}, {day['moving_hours']:g} hours")
        for part in day["segments"]:
            lines.append(f"  {part['name']}: {part['distance']:g} {unit} ({part['terrain']})")
        for save in day["forced_march_saves"]:
            lines.append(f"  Hour {save['after_hour']}: Constitution save DC {save['dc']}")
    lines.extend(["", *result["notes"]])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan overland travel using D&D 2014 rules.")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("gui", help="Open the desktop route planner")
    commands.add_parser("mcp", help="Run the optional MCP server over stdio")
    commands.add_parser("rules", help="Print the rule table and calculation assumptions as JSON")
    single = commands.add_parser("trip", help="Calculate one travel leg")
    single.add_argument("distance", type=float)
    single.add_argument("--unit", choices=("mi", "km"), default="mi")
    single.add_argument("--pace", choices=("slow", "normal", "fast", "custom"), default="normal")
    single.add_argument("--hours", type=float, default=8, help="Travel hours per day (default: 8)")
    single.add_argument("--basis", choices=("daily", "hourly"), default="daily")
    single.add_argument("--terrain", choices=("normal", "difficult"), default="normal")
    single.add_argument("--speed", type=float, help="Custom pace speed in selected units per hour")
    single.add_argument("--json", action="store_true", help="Print structured results")
    route = commands.add_parser("route", help="Calculate a saved JSON route")
    route.add_argument("path")
    route.add_argument("--json", action="store_true", help="Print structured results")
    args = parser.parse_args(argv)
    try:
        if args.command == "gui":
            from .gui import main as gui_main

            gui_main()
            return 0
        if args.command == "mcp":
            from .mcp_server import main as mcp_main

            mcp_main()
            return 0
        if args.command == "rules":
            print(json.dumps(rules(), indent=2))
            return 0
        if args.command == "route":
            journey = load_route(args.path)
        else:
            journey = Journey(
                (Leg("Journey", args.distance, args.terrain),),
                args.unit,
                args.pace,
                args.hours,
                args.basis,
                args.speed,
            )
        result = plan(journey)
        print(
            json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)
            if args.json
            else format_plan(result)
        )
        return 0
    except (ValidationError, OSError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
