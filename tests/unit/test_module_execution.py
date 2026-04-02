import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_python_m_cli_works_from_repo_root_without_install():
    result = subprocess.run(
        [sys.executable, "-m", "docspace_engine.cli", "--workspace", "D:/developItems", "status"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["state"] in ("cold", "stale", "hot")
