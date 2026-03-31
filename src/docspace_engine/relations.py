from __future__ import annotations

from collections import defaultdict
from typing import Callable

RELATION_FIELDS = [
    "implemented_by",
    "tested_by",
    "depends_on",
    "related_decisions",
    "supersedes",
    "superseded_by",
]

ITER_DOC_NODES: Callable[[], list[dict]] | None = None
GET_DOC_NODE: Callable[[str], dict | None] | None = None
LOAD_INDEX_MANIFEST: Callable[[], dict] | None = None
EXTRACT_FRONTMATTER: Callable[[str], dict] | None = None


def configure_relations_context(iter_doc_nodes, get_doc_node, load_index_manifest, extract_frontmatter):
    global ITER_DOC_NODES, GET_DOC_NODE, LOAD_INDEX_MANIFEST, EXTRACT_FRONTMATTER
    ITER_DOC_NODES = iter_doc_nodes
    GET_DOC_NODE = get_doc_node
    LOAD_INDEX_MANIFEST = load_index_manifest
    EXTRACT_FRONTMATTER = extract_frontmatter


def extract_relations_from_doc(filepath: str) -> dict:
    if EXTRACT_FRONTMATTER is None:
        return {}
    meta = EXTRACT_FRONTMATTER(filepath) or {}
    return {field: list(meta.get(field, []) or []) for field in RELATION_FIELDS}


def get_doc_relations(doc_id: str) -> dict:
    if GET_DOC_NODE is None:
        return {field: [] for field in RELATION_FIELDS}
    node = GET_DOC_NODE(doc_id) or {}
    return {field: list(node.get(field, []) or []) for field in RELATION_FIELDS}


def resolve_code_targets(doc_id: str) -> list[str]:
    return get_doc_relations(doc_id).get("implemented_by", [])


def resolve_test_targets(doc_id: str) -> list[str]:
    return get_doc_relations(doc_id).get("tested_by", [])


def get_related_decisions(doc_id: str) -> list[str]:
    return get_doc_relations(doc_id).get("related_decisions", [])


def build_reverse_lookup_index(iter_doc_nodes=None):
    iterator = iter_doc_nodes or ITER_DOC_NODES
    reverse = {"code_to_docs": defaultdict(list), "test_to_docs": defaultdict(list)}
    if iterator is None:
        return {"code_to_docs": {}, "test_to_docs": {}}

    for node in iterator() or []:
        doc_id = node.get("id")
        if not doc_id:
            continue
        for path in node.get("implemented_by", []) or []:
            reverse["code_to_docs"][path].append(doc_id)
        for path in node.get("tested_by", []) or []:
            reverse["test_to_docs"][path].append(doc_id)

    return {
        "code_to_docs": dict(reverse["code_to_docs"]),
        "test_to_docs": dict(reverse["test_to_docs"]),
    }


def infer_doc_links_for_path(path: str, iter_doc_nodes=None) -> list[dict]:
    iterator = iter_doc_nodes or ITER_DOC_NODES
    if iterator is None:
        return []
    matches = []
    filename = path.replace('\\', '/').split('/')[-1]
    for node in iterator() or []:
        doc_id = node.get("id")
        if not doc_id:
            continue
        targets = [*(node.get("implemented_by", []) or []), *(node.get("tested_by", []) or [])]
        if any(filename and filename in target for target in targets):
            matches.append({
                "doc_id": doc_id,
                "reason": path,
                "link_type": "inferred",
            })
    return matches
