import subprocess
import sys
from pathlib import Path

def test_console_script_is_registered():
    # This test verifies that the script is defined in pyproject.toml
    # by checking the content for the correct entrypoint definition.
    root = Path(__file__).resolve().parents[2]
    pyproject_path = root / "pyproject.toml"
    assert pyproject_path.exists(), f"pyproject.toml not found at {pyproject_path}"

    pyproject_content = pyproject_path.read_text(encoding="utf-8")
    assert '[project.scripts]' in pyproject_content, "[project.scripts] section missing in pyproject.toml"
    assert 'docspace-engine = "docspace_engine.cli:main"' in pyproject_content, "docspace-engine entrypoint missing or incorrect"
