import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_WORKSPACE = ROOT / ".." / "examples" / "example-workspace"
SRC_ROOT = ROOT / ".." / "src"


def _run_cli(*args: str):
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(SRC_ROOT) if not existing else f"{SRC_ROOT}{os.pathsep}{existing}"
    return subprocess.run(
        [sys.executable, "-m", "docspace_engine.cli", "--workspace", str(EXAMPLE_WORKSPACE), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_cli_supports_status_impact_and_retrieve_v2_against_example_workspace():
    status = _run_cli("status")
    assert status.returncode == 0
    assert json.loads(status.stdout)["state"] == "ready"

    impact = _run_cli("impact", "--paths", "src/sidebar.js")
    assert impact.returncode == 0
    assert json.loads(impact.stdout)["impacted_docs"][0]["doc_id"] == "sidebar-arch"

    retrieve = _run_cli("retrieve-v2", "--query", "sidebar", "--budget", "small", "--changed-paths", "src/sidebar.js")
    assert retrieve.returncode == 0
    payload = json.loads(retrieve.stdout)
    assert payload["facts"]["current"]["id"] == "sidebar-arch"
    assert payload["trust"]["status"] == "impacted"
