"""Install the wheel outside the checkout and exercise the installed commands."""

import json
import os
import subprocess
import tempfile
import venv
from pathlib import Path

wheel = next(Path("dist").glob("calculator_5e-*.whl")).resolve()
with tempfile.TemporaryDirectory(prefix="calculator-5e-package-") as directory:
    root = Path(directory)
    environment = root / "venv"
    venv.EnvBuilder(with_pip=True).create(environment)
    scripts = environment / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    command = scripts / ("calculator-5e.exe" if os.name == "nt" else "calculator-5e")
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    subprocess.run(
        [str(python), "-m", "pip", "install", "--no-deps", str(wheel)],
        cwd=root,
        env=env,
        check=True,
    )
    result = subprocess.run(
        [str(command), "trip", "24", "--json"],
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=True,
        timeout=15,
    )
    assert json.loads(result.stdout)["moving_hours"] == 8
    missing = subprocess.run(
        [str(command), "mcp"], cwd=root, env=env, text=True, capture_output=True, timeout=15
    )
    assert missing.returncode == 2, missing.stderr
    assert "optional" in missing.stderr and "Traceback" not in missing.stderr
    print("Wheel installed; CLI calculation and optional-dependency error verified.")
