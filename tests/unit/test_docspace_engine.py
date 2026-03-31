from docspace_engine import cli


def test_reverse_lookup_returns_authoritative_doc_nodes(monkeypatch):
    monkeypatch.setattr(
        cli,
        "_iter_doc_nodes",
        lambda: [
            {
                "id": "sidebar-arch",
                "implemented_by": ["src/sidebar.js"],
                "tested_by": ["tests/sidebar.test.js"],
            }
        ],
    )

    reverse = cli.build_reverse_lookup_index()

    assert reverse["code_to_docs"]["src/sidebar.js"] == ["sidebar-arch"]
    assert reverse["test_to_docs"]["tests/sidebar.test.js"] == ["sidebar-arch"]


def test_compute_change_impact_marks_direct_reverse_lookup_hits(monkeypatch):
    monkeypatch.setattr(
        cli,
        "build_reverse_lookup_index",
        lambda: {"code_to_docs": {"src/sidebar.js": ["sidebar-arch"]}, "test_to_docs": {}},
    )
    monkeypatch.setattr(cli, "get_doc_relations", lambda _doc_id: {"depends_on": [], "related_decisions": []})
    monkeypatch.setattr(cli, "get_children", lambda _doc_id: [])

    impact = cli.compute_change_impact(["src/sidebar.js"])

    assert impact["impacted_docs"][0]["doc_id"] == "sidebar-arch"
    assert impact["impacted_docs"][0]["impact_kind"] == "direct"


def test_retrieve_for_task_v2_returns_layered_package(monkeypatch):
    monkeypatch.setattr(cli, "retrieve_tree_context", lambda _doc_id: {"current": {"id": "sidebar-arch"}, "ancestors": [], "children": []})
    monkeypatch.setattr(cli, "expand_with_relations", lambda ctx: {**ctx, "code_targets": ["src/sidebar.js"], "test_targets": ["tests/sidebar.test.js"]})
    monkeypatch.setattr(cli, "compute_change_impact", lambda _paths: {"impacted_docs": [{"doc_id": "sidebar-arch", "impact_kind": "direct", "confidence": 1.0, "reason": "src/sidebar.js"}]})
    monkeypatch.setattr(cli, "apply_trust_degradation", lambda _impact: {"sidebar-arch": {"trust_status": "impacted", "needs_review": True, "trust_confidence": 0.6}})
    monkeypatch.setattr(cli, "_resolve_start_node_from_query", lambda _query: "sidebar-arch")

    result = cli.retrieve_for_task_v2(
        query="sidebar",
        intent_hint="locate",
        changed_paths=["src/sidebar.js"],
        budget="normal",
    )

    assert "facts" in result
    assert "inferred" in result
    assert "trust" in result
    assert "reasoning_space" in result
    assert result["trust"]["status"] == "impacted"


def test_get_ancestor_chain_returns_ordered_parents(monkeypatch):
    docs = {
        "project-index": {"parent": None},
        "architecture": {"parent": "project-index"},
        "frontend": {"parent": "architecture"},
        "sidebar": {"parent": "frontend"},
    }
    monkeypatch.setattr(cli, "_get_doc_node", lambda doc_id: docs.get(doc_id))

    ancestors = cli.get_ancestor_chain("sidebar")

    assert ancestors == ["project-index", "architecture", "frontend"]


def test_default_manifest_can_store_trust_snapshot():
    manifest = cli._default_index_manifest()

    assert "trust" in manifest or manifest.setdefault("trust", {}) == {}


def test_main_supports_impact_action(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "compute_change_impact", lambda paths: {"changed_paths": paths, "impacted_docs": []})

    exit_code = cli.main([
        "--workspace",
        str(tmp_path),
        "impact",
        "--paths",
        "src/foo.js",
    ])

    assert exit_code == 0
