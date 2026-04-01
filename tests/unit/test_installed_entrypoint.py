import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_installed_module_works_from_outside_repo():
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", str(ROOT)],
        capture_output=True,
        text=True,
        check=True,
    )

    result = subprocess.run(
        ["docspace-engine", "--workspace", "D:/developItems", "status"],
        cwd="D:/developItems",
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["state"] == "ready"
