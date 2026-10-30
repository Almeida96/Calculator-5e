# MCP integration

The optional stdio server lets an MCP-compatible agent call the calculator. It uses the official Python MCP SDK's 1.x API, bounded below version 2 to avoid an incompatible upgrade.

Install it in the interpreter your client will launch:

```sh
python -m pip install ".[mcp]"
```

There is no HTTP port, model provider, API key or background service. The MCP client starts the process and communicates over stdin/stdout. Protocol output stays on stdout; SDK diagnostics use stderr.

## Client configuration

For clients that accept an `mcpServers` JSON configuration:

```json
{
  "mcpServers": {
    "calculator-5e": {
      "command": "/absolute/path/to/Calculator-5e/.venv/bin/python",
      "args": ["-m", "calculator_5e", "mcp"]
    }
  }
}
```

On Windows, replace `command` with the interpreter path, escaping backslashes:

```json
{
  "command": "C:\\path\\to\\Calculator-5e\\.venv\\Scripts\\python.exe",
  "args": ["-m", "calculator_5e", "mcp"]
}
```

Client configuration files differ. Use the equivalent stdio-server fields for your client. Install the package first so launching from a different working directory works.

## Tools

| Tool | Input | Result |
| --- | --- | --- |
| `plan_journey` | A `journey` object | Daily itinerary, totals, saves, assumptions |
| `compare_paces` | A `journey` object | Slow/normal/fast summaries for the same route |
| `travel_rules` | No arguments | Rule table, source and modelling limits |

The journey fields match the [route format](usage.md#route-format). MCP defaults `schema_version` to 1 if omitted. Numeric strings, unknown fields and invalid numeric ranges are rejected.

`plan_journey` limits output to 365 travel days. `compare_paces` returns summaries and uses the core's 10,000-day limit for each pace. It compares the three standard paces even when the input uses a valid custom speed.

All three tools are declared read-only and idempotent. They do not open paths, run commands or access the network. Route names remain labels in results, not instructions. A client may still send those labels to its configured model provider.

## Example

Ask an agent:

> Plan 12 miles along a road, 9 miles through difficult forest and 6 miles to the keep. Use normal pace, eight hours per day and the daily table. Compare the other paces too, and explain your assumptions.

The calculation tool arguments are:

```json
{
  "journey": {
    "unit": "mi",
    "pace": "normal",
    "hours_per_day": 8,
    "basis": "daily",
    "legs": [
      {"name": "Road", "distance": 12},
      {"name": "Forest", "distance": 9, "terrain": "difficult"},
      {"name": "Keep", "distance": 6}
    ]
  }
}
```

Expected normal-pace result: two travel days, 12 moving hours, and four hours on the final day. No forced-march saves are due. The agent should cite the daily interpolation assumption rather than present an exact arrival time.

The integration test verifies discovery, tool annotations, structured calculation results, pace comparison, rules lookup, invalid-input rejection and recovery after errors using a real subprocess:

```sh
python -m unittest tests.test_mcp -v
```

This tests the protocol and calculations. It does not measure a language model's choice of tools or answer quality.
