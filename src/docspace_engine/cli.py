from __future__ import annotations

import argparse
import json
from pathlib import Path

from .impact import compute_change_impact as _module_compute_change_impact
from .impact import configure_impact_context
from .relations import (
    RELATION_FIELDS,
    build_reverse_lookup_index as _module_build_reverse_lookup_index,
    configure_relations_context,
    get_doc_relations as _module_get_doc_relations,
)
from .retrieval import configure_retrieval_context
from .retrieval import retrieve_for_task_v2 as _module_retrieve_for_task_v2
from .tree import build_subtree_summary, configure_tree_context
from .tree import get_children as _module_get_children
from .trust import apply_trust_degradation as _module_apply_trust_degradation

PROJECT_ROOT = "."


def _extract_frontmatter(filepath: str) -> dict:
    text = Path(filepath).read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    meta = {}
    key = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("  - ") and key:
            meta.setdefault(key, []).append(line[4:].strip())
            continue
        if ":" in line:
            raw_key, raw_value = line.split(":", 1)
            key = raw_key.strip()
            value = raw_value.strip()
            if value == "":
                meta[key] = []
            else:
                meta[key] = value
    return meta


def _extract_title(filepath: str) -> str:
    """Extract the first H1 title from markdown body."""
    try:
        text = Path(filepath).read_text(encoding="utf-8")
    except Exception:
        return Path(filepath).stem
    # Skip frontmatter
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                start = i + 1
                break
    # Find first H1
    for line in lines[start:]:
        if line.startswith("# "):
            return line[2:].strip()
    return Path(filepath).stem


def _extract_summary(filepath: str) -> str:
    """Extract the first non-empty paragraph from markdown body, truncated to 200 chars."""
    try:
        text = Path(filepath).read_text(encoding="utf-8")
    except Exception:
        return ""
    lines = text.splitlines()
    # Skip frontmatter
    start = 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                start = i + 1
                break
    # Collect first non-empty, non-heading paragraph
    paragraph_lines = []
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped:
            if paragraph_lines:
                break
            continue
        if stripped.startswith("#"):
            if paragraph_lines:
                break
            continue
        paragraph_lines.append(stripped)
    summary = " ".join(paragraph_lines)
    return summary[:200]


import re
from typing import Set


def _tokenize(text: str) -> Set[str]:
    """Normalize text to lowercase tokens, splitting on non-alphanumeric."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _iter_doc_nodes():
    docs_root = Path(PROJECT_ROOT) / "docs"
    if not docs_root.exists():
        return []
    nodes = []
    for path in sorted(docs_root.rglob("*.md")):
        meta = _extract_frontmatter(str(path))
        if not meta.get("id"):
            continue
        rel_path = str(path.relative_to(Path(PROJECT_ROOT))).replace("\\", "/")
        nodes.append({"id": meta["id"], "path": rel_path, **meta})
    return nodes


def _get_doc_node(doc_id: str):
    for node in _iter_doc_nodes():
        if node.get("id") == doc_id:
            return node
    return None


def _load_index_manifest() -> dict:
    return _default_index_manifest()


def _default_index_manifest() -> dict:
    return {"trust": {}, "last_impact": {}}


def _build_searchable_text(node: dict) -> str:
    """Build a searchable blob from all relevant doc fields."""
    parts = [
        node.get("id", ""),
        node.get("type", ""),
        node.get("parent", ""),
        node.get("_title", ""),
        node.get("_summary", ""),
    ]
    # Flatten list fields
    for field in ("implemented_by", "tested_by"):
        vals = node.get(field)
        if isinstance(vals, list):
            parts.extend(vals)
        elif vals:
            parts.append(str(vals))
    return " ".join(str(p) for p in parts)


def _resolve_start_node_from_query(query: str) -> str | None:
    """Multi-field token-matching query resolver.

    Tokenize the query, then score each doc node by how many query tokens
    appear in its searchable text. Return the doc_id with the highest score,
    or None if no tokens match at all.
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return None

    best_id: str | None = None
    best_score = 0

    for node in _iter_doc_nodes():
        doc_id = node.get("id")
        if not doc_id:
            continue
        # Enrich node with title and summary for matching
        node["_title"] = _extract_title(str(Path(PROJECT_ROOT) / node.get("path", ""))) if node.get("path") else ""
        node["_summary"] = _extract_summary(str(Path(PROJECT_ROOT) / node.get("path", ""))) if node.get("path") else ""

        searchable = _build_searchable_text(node)
        doc_tokens = _tokenize(searchable)
        score = len(query_tokens & doc_tokens)
        if score > best_score:
            best_score = score
            best_id = doc_id

    return best_id


def retrieve_tree_context(doc_id: str | None) -> dict:
    if not doc_id:
        return {"current": None, "ancestors": [], "children": []}
    summary = build_subtree_summary(doc_id, depth=1)
    return {
        "current": summary.get("current"),
        "ancestors": summary.get("ancestors", []),
        "children": summary.get("children", []),
    }


def expand_with_relations(ctx: dict) -> dict:
    current = ctx.get("current") or {}
    doc_id = current.get("id")
    expanded = dict(ctx)
    if not doc_id:
        expanded["code_targets"] = []
        expanded["test_targets"] = []
        expanded["inferred"] = []
        return expanded
    relations = get_doc_relations(doc_id)
    expanded["code_targets"] = list(relations.get("implemented_by", []) or [])
    expanded["test_targets"] = list(relations.get("tested_by", []) or [])
    expanded["inferred"] = []
    return expanded


def _sync_context():
    configure_tree_context(PROJECT_ROOT, _extract_frontmatter, _extract_title, _extract_summary)
    configure_relations_context(_iter_doc_nodes, _get_doc_node, _load_index_manifest, _extract_frontmatter)
    configure_impact_context(build_reverse_lookup_index, get_doc_relations, get_children)
    configure_retrieval_context(
        retrieve_tree_context,
        expand_with_relations,
        compute_change_impact,
        apply_trust_degradation,
        _resolve_start_node_from_query,
    )


def build_reverse_lookup_index():
    _sync_context()
    return _module_build_reverse_lookup_index(_iter_doc_nodes)


def get_doc_relations(doc_id: str) -> dict:
    _sync_context()
    return _module_get_doc_relations(doc_id)


def get_children(doc_id: str) -> list[str]:
    _sync_context()
    return _module_get_children(doc_id)


def get_ancestor_chain(doc_id: str) -> list[str]:
    ancestors = []
    current = _get_doc_node(doc_id)
    seen = set()
    while current and current.get("parent") and current["parent"] not in seen:
        parent_id = current["parent"]
        ancestors.append(parent_id)
        seen.add(parent_id)
        current = _get_doc_node(parent_id)
    return list(reversed(ancestors))


def compute_change_impact(changed_paths: list[str]) -> dict:
    _sync_context()
    return _module_compute_change_impact(changed_paths)


def apply_trust_degradation(impact_report: dict) -> dict:
    return _module_apply_trust_degradation(impact_report)


def retrieve_for_task_v2(
    query: str,
    intent_hint: str = "locate",
    start_doc_id: str | None = None,
    changed_paths: list[str] | None = None,
    budget: str = "normal",
) -> dict:
    _sync_context()
    return _module_retrieve_for_task_v2(
        query=query,
        intent_hint=intent_hint,
        start_doc_id=start_doc_id,
        changed_paths=changed_paths,
        budget=budget,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="docspace-engine")
    parser.add_argument("--workspace", default=".")
    subparsers = parser.add_subparsers(dest="action", required=True)

    subparsers.add_parser("status")

    impact_parser = subparsers.add_parser("impact")
    impact_parser.add_argument("--paths", nargs="+", required=True)

    retrieve_parser = subparsers.add_parser("retrieve-v2")
    retrieve_parser.add_argument("--query", required=True)
    retrieve_parser.add_argument("--budget", default="normal")
    retrieve_parser.add_argument("--changed-paths", nargs="*", default=[])

    return parser


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    global PROJECT_ROOT
    PROJECT_ROOT = args.workspace

    if args.action == "status":
        print(json.dumps({"state": "ready", "workspace": PROJECT_ROOT}, ensure_ascii=False))
        return 0

    if args.action == "impact":
        print(json.dumps(compute_change_impact(args.paths), ensure_ascii=False))
        return 0

    if args.action == "retrieve-v2":
        print(
            json.dumps(
                retrieve_for_task_v2(
                    query=args.query,
                    changed_paths=args.changed_paths,
                    budget=args.budget,
                ),
                ensure_ascii=False,
            )
        )
        return 0

    return 0


__all__ = [
    "RELATION_FIELDS",
    "PROJECT_ROOT",
    "_default_index_manifest",
    "_get_doc_node",
    "_iter_doc_nodes",
    "apply_trust_degradation",
    "build_reverse_lookup_index",
    "compute_change_impact",
    "get_ancestor_chain",
    "get_children",
    "get_doc_relations",
    "main",
    "retrieve_for_task_v2",
]


if __name__ == "__main__":
    raise SystemExit(main())
