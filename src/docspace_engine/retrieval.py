from __future__ import annotations

from copy import deepcopy
from typing import Callable

BUDGET_PRESETS = {
    "small": {"max_inferred": 1},
    "normal": {"max_inferred": 3},
    "deep": {"max_inferred": 6},
}

RETRIEVE_TREE_CONTEXT: Callable[[str], dict] | None = None
EXPAND_WITH_RELATIONS: Callable[[dict], dict] | None = None
COMPUTE_CHANGE_IMPACT: Callable[[list[str]], dict] | None = None
APPLY_TRUST_DEGRADATION: Callable[[dict], dict] | None = None
RESOLVE_START_NODE_FROM_QUERY: Callable[[str], str | None] | None = None


def configure_retrieval_context(
    retrieve_tree_context,
    expand_with_relations,
    compute_change_impact,
    apply_trust_degradation,
    resolve_start_node_from_query,
):
    global RETRIEVE_TREE_CONTEXT, EXPAND_WITH_RELATIONS, COMPUTE_CHANGE_IMPACT, APPLY_TRUST_DEGRADATION, RESOLVE_START_NODE_FROM_QUERY
    RETRIEVE_TREE_CONTEXT = retrieve_tree_context
    EXPAND_WITH_RELATIONS = expand_with_relations
    COMPUTE_CHANGE_IMPACT = compute_change_impact
    APPLY_TRUST_DEGRADATION = apply_trust_degradation
    RESOLVE_START_NODE_FROM_QUERY = resolve_start_node_from_query


def _apply_budget(package: dict, budget: str) -> dict:
    limited = deepcopy(package)
    preset = BUDGET_PRESETS.get(budget, BUDGET_PRESETS["normal"])
    inferred = list(limited.get("inferred", []))
    limited["inferred"] = inferred[: preset["max_inferred"]]
    return limited


def retrieve_for_task_v2(
    query: str,
    intent_hint: str = "locate",
    start_doc_id: str | None = None,
    changed_paths: list[str] | None = None,
    budget: str = "normal",
) -> dict:
    doc_id = start_doc_id or (RESOLVE_START_NODE_FROM_QUERY(query) if RESOLVE_START_NODE_FROM_QUERY else None)
    tree_context = RETRIEVE_TREE_CONTEXT(doc_id) if RETRIEVE_TREE_CONTEXT and doc_id else {"current": None, "ancestors": [], "children": []}
    expanded = EXPAND_WITH_RELATIONS(tree_context) if EXPAND_WITH_RELATIONS else dict(tree_context)
    impact_report = COMPUTE_CHANGE_IMPACT(changed_paths or []) if COMPUTE_CHANGE_IMPACT else {"impacted_docs": []}
    trust_map = APPLY_TRUST_DEGRADATION(impact_report) if APPLY_TRUST_DEGRADATION else {}
    trust = trust_map.get(doc_id, {"trust_status": "fresh", "needs_review": False, "trust_confidence": 1.0}) if doc_id else {"trust_status": "fresh", "needs_review": False, "trust_confidence": 1.0}

    package = {
        "query": query,
        "intent_hint": intent_hint,
        "facts": {
            "current": expanded.get("current"),
            "ancestors": expanded.get("ancestors", []),
            "children": expanded.get("children", []),
            "code_targets": expanded.get("code_targets", []),
            "test_targets": expanded.get("test_targets", []),
        },
        "inferred": expanded.get("inferred", []),
        "trust": {
            "status": trust.get("trust_status", "fresh"),
            "needs_review": trust.get("needs_review", False),
            "confidence": trust.get("trust_confidence", 1.0),
        },
        "reasoning_space": {
            "changed_paths": changed_paths or [],
            "impact": impact_report.get("impacted_docs", []),
        },
    }
    return _apply_budget(package, budget)
