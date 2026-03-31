from pathlib import Path

from docspace_engine import cli


FIXTURE_ROOT = Path(__file__).resolve().parent.parent / "fixtures" / "workspace"


def test_fake_workspace_supports_impact_and_retrieve_v2():
    cli.PROJECT_ROOT = str(FIXTURE_ROOT)

    impact = cli.compute_change_impact(["src/sidebar.js"])
    assert impact["impacted_docs"]
    assert impact["impacted_docs"][0]["doc_id"] == "sidebar-arch"

    result = cli.retrieve_for_task_v2(
        query="sidebar",
        intent_hint="locate",
        changed_paths=["src/sidebar.js"],
        budget="small",
    )

    assert result["facts"]["current"]["id"] == "sidebar-arch"
    assert result["facts"]["code_targets"] == ["src/sidebar.js"]
    assert result["facts"]["test_targets"] == ["tests/sidebar.test.js"]
    assert result["trust"]["status"] == "impacted"
    assert result["reasoning_space"]["impact"]
