# Changelog

## 1.0.0 — 2026-10-30

The original single-window calculator is now an overland route planner.

- Add editable, reorderable route legs with normal or difficult terrain.
- Add 2014 slow, normal and fast travel paces, explicit daily/hourly calculation bases, and custom speeds.
- Show a daily itinerary, moving hours and forced-march saving throw DCs.
- Convert between miles and kilometers in the desktop editor.
- Save and reopen versioned JSON routes; export calculated results.
- Add CLI commands and optional read-only MCP tools for agent use.
- Reject zero travel hours, negative distances, nonfinite values and invalid route files.
- Separate calculations from Tkinter; importing modules no longer starts the interface.
- Add automated core, storage, GUI, CLI and MCP tests, package checks and CI.
- Add installation, usage, rules, MCP and architecture documentation in English.
- Remove tracked IDE configuration.

### Migrating from the original calculator

`python main.py` still starts the desktop app. Numeric movement-mode inputs have been replaced with named paces.

The old defaults used constant speeds of 3.6, 6, 15, 20 and 55 km/h. They were not tied to a documented edition's travel table. Use **custom** pace and enter one of these speeds if it represents a house rule for your game.

Results now distinguish the number of travel days from total moving hours. A journey using ten hours of an eight-hour travel schedule takes two travel days, with two hours on its final day. It is no longer displayed only as a fractional number of days.
