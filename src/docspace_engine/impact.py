from __future__ import annotations

from typing import Callable

BUILD_REVERSE_LOOKUP_INDEX: Callable[[], dict] | None = None
GET_DOC_RELATIONS: Callable[[str], dict] | None = None
GET_CHILDREN: Callable[[str], list[str]] | None = None


def configure_impact_context(build_reverse_lookup_index, get_doc_relations, get_children):
    global BUILD_REVERSE_LOOKUP_INDEX, GET_DOC_RELATIONS, GET_CHILDREN
    BUILD_REVERSE_LOOKUP_INDEX = build_reverse_lookup_index
    GET_DOC_RELATIONS = get_doc_relations
    GET_CHILDREN = get_children


def compute_change_impact(changed_paths: list[str]) -> dict:
    reverse = BUILD_REVERSE_LOOKUP_INDEX() if BUILD_REVERSE_LOOKUP_INDEX else {"code_to_docs": {}, "test_to_docs": {}}
    impacted = []
    seen = set()

    def _add(doc_id: str, impact_kind: str, confidence: float, reason: str):
        key = (doc_id, impact_kind, reason)
        if key in seen:
            return
        seen.add(key)
        impacted.append({
            "doc_id": doc_id,
            "impact_kind": impact_kind,
            "confidence": confidence,
            "reason": reason,
        })

    for path in changed_paths:
        for doc_id in reverse.get("code_to_docs", {}).get(path, []):
            _add(doc_id, "direct", 1.0, path)
            if GET_DOC_RELATIONS:
                relations = GET_DOC_RELATIONS(doc_id) or {}
                for dep in relations.get("depends_on", []) or []:
                    _add(dep, "dependency", 0.7, doc_id)
            if GET_CHILDREN:
                for child in GET_CHILDREN(doc_id) or []:
                    _add(child, "descendant", 0.6, doc_id)
        for doc_id in reverse.get("test_to_docs", {}).get(path, []):
            _add(doc_id, "direct", 1.0, path)

    return {"changed_paths": changed_paths, "impacted_docs": impacted}
