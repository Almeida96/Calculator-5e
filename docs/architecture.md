# Architecture

All interfaces call the same pure calculation function:

```text
Tkinter GUI ─┐
CLI ─────────┼── Journey / Leg validation ── plan() ── itinerary
MCP tools ───┘
                  │
             JSON route storage
```

| Module | Responsibility |
| --- | --- |
| `calculator_5e/core.py` | Immutable inputs, validation, rule table, scheduling |
| `calculator_5e/storage.py` | Bounded JSON reads, duplicate-key checks, atomic route replacement |
| `calculator_5e/gui.py` | Route editor, unit conversion, file dialogs and itinerary display |
| `calculator_5e/cli.py` | Argument parsing, readable/JSON output and exit status |
| `calculator_5e/mcp_server.py` | Optional SDK models and read-only stdio tools |
| `main.py` | Compatibility launcher for the original desktop command |

## Scheduling

The engine traverses legs in order. Each allocation stops at the next leg end, travel-day end or eight-hour rate boundary. A terrain multiplier applies to that allocation's speed. Day totals and forced-march checks are calculated after all allocations for that day.

Inputs are converted from their decimal representation to `Fraction`. This avoids floating-point drift adding an extra travel day or triggering a save early. Only serialized output is rounded, to six decimal places.

The route limit is 100 legs and the schedule limit is 10,000 days. There is no persistence, clock or random input in the calculation function, so identical inputs produce identical outputs.

## Interface boundaries

The core and CLI have no third-party dependencies. Tkinter is imported only by the GUI module. Importing the desktop launcher does not create a window.

MCP imports its SDK inside the server factory, so installations without the optional extra can still use the CLI and desktop app. Tool input validation supplies a discoverable JSON Schema; core validation remains authoritative.

Route files carry `schema_version: 1`. Unknown fields are rejected to catch misspelled settings. Result files have a separate shape and cannot be reopened as routes.

## Verification

Core tests cover both pace tables, terrain transitions, decimal boundaries, unit conversion, overtime and invalid inputs. Storage tests check round trips and preservation of an existing file after a failed replacement. GUI tests exercise editing, unit conversion, invalidation and file-loading behavior. CLI and MCP tests start subprocesses.

CI also installs the built wheel in a clean environment outside the checkout, runs the installed CLI and checks that missing MCP dependencies produce a useful error. This catches packaging failures that source-tree tests miss.
