# Contributing

Use Python 3.11 or newer and a virtual environment:

```sh
python -m pip install -e ".[mcp,dev]"
python -m unittest discover -s tests -v
python -m ruff check .
python -m ruff format --check .
```

Run GUI tests with a desktop display or Xvfb. CI sets `CALCULATOR_REQUIRE_GUI_TESTS=1`, so missing display support fails rather than silently skipping the GUI suite.

For a calculation change, include a worked example, a reference to the relevant rule edition, and a regression test. Keep house-rule assumptions separate from rules quoted in the travel table. Changing the route format requires a versioning decision and updates to the schema, example and user guide.

Keep arithmetic out of the GUI, CLI and MCP adapters. New adapters should call the core instead of maintaining another set of formulas.

Before changing packaging:

```sh
python -m build
python tools/smoke_package.py
```

Describe the behavior changed in the pull request and list the checks you ran. For bug reports, include the Python version, operating system, command or route input, expected result and actual result. Remove private campaign details before sharing a route.
