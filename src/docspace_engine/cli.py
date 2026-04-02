from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
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


def _extract_body(filepath: str, max_chars: int = 2000) -> str:
    """Extract body text from markdown (excluding frontmatter), truncated to max_chars."""
    try:
        text = Path(filepath).read_text(encoding="utf-8")
    except Exception:
        return ""
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                start = i + 1
                break
    # Collect body lines, strip markdown syntax
    body_lines = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("```"):
            continue
        body_lines.append(stripped)
    body = " ".join(body_lines)
    return body[:max_chars]


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
    """Normalize text to lowercase tokens. Handles CJK characters as individual tokens."""
    # Match ASCII words, or individual CJK characters, or digits
    tokens = set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text.lower()))
    return tokens


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
        node.get("_body", ""),
    ]
    # Flatten list fields
    for field in ("implemented_by", "tested_by"):
        vals = node.get(field)
        if isinstance(vals, list):
            parts.extend(vals)
        elif vals:
            parts.append(str(vals))
    return " ".join(str(p) for p in parts)


def _score_node(query_tokens: set, node: dict) -> int:
    """Score a node against query tokens with field weights.

    Field weights:
      id, title            → 5 (most precise)
      summary, list fields → 2 (good signal, short)
      body                 → 1 (largest, noisiest)
    """
    score = 0

    # Weight 5: id + title
    id_title = _tokenize(f"{node.get('id', '')} {node.get('_title', '')}")
    score += 5 * len(query_tokens & id_title)

    # Weight 2: summary
    summary_tokens = _tokenize(node.get("_summary", ""))
    score += 2 * len(query_tokens & summary_tokens)

    # Weight 2: list fields
    for field in ("implemented_by", "tested_by"):
        vals = node.get(field)
        if isinstance(vals, list):
            field_tokens = _tokenize(" ".join(str(v) for v in vals))
        elif vals:
            field_tokens = _tokenize(str(vals))
        else:
            continue
        score += 2 * len(query_tokens & field_tokens)

    # Weight 1: body
    body_tokens = _tokenize(node.get("_body", ""))
    score += len(query_tokens & body_tokens)

    return score


def _resolve_start_node_from_query(query: str) -> str | None:
    """Multi-field weighted token-matching query resolver."""
    query_tokens = _tokenize(query)
    if not query_tokens:
        return None

    best_id: str | None = None
    best_score = 0

    for node in _iter_doc_nodes():
        doc_id = node.get("id")
        if not doc_id:
            continue
        filepath = str(Path(PROJECT_ROOT) / node.get("path", "")) if node.get("path") else ""
        node["_title"] = _extract_title(filepath)
        node["_summary"] = _extract_summary(filepath)
        node["_body"] = _extract_body(filepath)

        score = _score_node(query_tokens, node)
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

    index_parser = subparsers.add_parser("index")
    index_parser.add_argument(
        "--path", required=False, default="docs/project-index.md",
        help="Path to project index for creating the index/warmup",
    )

    warmup_parser = subparsers.add_parser("warmup")
    warmup_parser.add_argument(
        "--path", required=False, default="docs/project-index.md",
        help="Path to warmup index (optional)",
    )

    reindex_parser = subparsers.add_parser("reindex")

    validate_parser = subparsers.add_parser("validate")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--budget", default="normal")
    search_parser.add_argument("--changed-paths", nargs="*", default=[])

    retrieve_parser = subparsers.add_parser("retrieve-v2")
    retrieve_parser.add_argument("--query", required=True)
    retrieve_parser.add_argument("--budget", default="normal")
    retrieve_parser.add_argument("--changed-paths", nargs="*", default=[])

    return parser


def _get_index_path() -> Path:
    """Path to the lightweight index manifest file."""
    return Path(PROJECT_ROOT) / ".docspace" / "index.json"


def _compute_index_state() -> str:
    """Determine index freshness: cold, stale, or hot.

    cold  — no index file exists yet
    stale — index exists but docs have been modified since indexing
    hot   — index exists and is up-to-date
    """
    index_path = _get_index_path()
    if not index_path.exists():
        return "cold"

    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception:
        return "cold"

    indexed_at = data.get("indexed_at")
    if not indexed_at:
        return "cold"

    # Check if any doc file is newer than the index
    docs_root = Path(PROJECT_ROOT) / "docs"
    if not docs_root.exists():
        return "cold"

    from datetime import datetime, timezone
    try:
        idx_time = datetime.fromisoformat(indexed_at)
        if idx_time.tzinfo is None:
            idx_time = idx_time.replace(tzinfo=timezone.utc)
    except Exception:
        return "cold"

    for md_path in docs_root.rglob("*.md"):
        try:
            mtime = datetime.fromtimestamp(md_path.stat().st_mtime, tz=timezone.utc)
            if mtime > idx_time:
                return "stale"
        except Exception:
            continue
    return "hot"


def _build_index() -> dict:
    """Build a lightweight index: doc nodes with titles and summaries."""
    nodes = _iter_doc_nodes()
    index_data = {
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        "doc_count": len(nodes),
        "docs": [],
    }
    for node in nodes:
        entry = {
            "id": node.get("id"),
            "path": node.get("path", ""),
            "parent": node.get("parent", ""),
            "type": node.get("type", ""),
        }
        filepath = str(Path(PROJECT_ROOT) / node.get("path", "")) if node.get("path") else ""
        if filepath:
            entry["title"] = _extract_title(filepath)
            entry["summary"] = _extract_summary(filepath)
        # Flatten list fields for index
        for field in ("implemented_by", "tested_by"):
            vals = node.get(field)
            entry[field] = vals if isinstance(vals, list) else []
        index_data["docs"].append(entry)
    return index_data


def _write_index(index_data: dict) -> Path:
    """Write index to .docspace/index.json, creating directory if needed."""
    index_path = _get_index_path()
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return index_path


def _validate_doc_tree() -> dict:
    """Validate doc tree integrity: orphan detection, missing parents, required fields."""
    nodes = _iter_doc_nodes()
    node_ids = {n.get("id") for n in nodes if n.get("id")}
    issues = []
    for node in nodes:
        doc_id = node.get("id")
        # Required fields
        for field in ("id", "type", "status", "maturity"):
            if not node.get(field):
                issues.append({"id": doc_id or "(unknown)", "issue": f"missing required field: {field}"})
        # Parent existence
        parent = node.get("parent")
        if parent and parent not in node_ids:
            issues.append({"id": doc_id, "issue": f"parent '{parent}' not found in doc tree"})
        # Orphan detection (non-root without parent)
        if doc_id and doc_id != "project-index" and not parent:
            issues.append({"id": doc_id, "issue": "orphan document (no parent)"})
    return {"valid": len(issues) == 0, "total_docs": len(nodes), "issues": issues}


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    global PROJECT_ROOT
    PROJECT_ROOT = args.workspace

    if args.action == "status":
        state = _compute_index_state()
        print(json.dumps({"state": state, "workspace": PROJECT_ROOT}, ensure_ascii=False))
        return 0

    if args.action == "index":
        index_data = _build_index()
        _write_index(index_data)
        print(json.dumps({
            "state": "hot",
            "workspace": PROJECT_ROOT,
            "indexed_docs": index_data["doc_count"],
        }, ensure_ascii=False))
        return 0

    if args.action == "warmup":
        # Warmup is an alias for index — builds index and reports readiness
        index_data = _build_index()
        _write_index(index_data)
        print(json.dumps({
            "state": "hot",
            "workspace": PROJECT_ROOT,
            "warmed_up": True,
            "indexed_docs": index_data["doc_count"],
        }, ensure_ascii=False))
        return 0

    if args.action == "reindex":
        index_data = _build_index()
        _write_index(index_data)
        print(json.dumps({
            "state": "hot",
            "workspace": PROJECT_ROOT,
            "reindexed_docs": index_data["doc_count"],
        }, ensure_ascii=False))
        return 0

    if args.action == "validate":
        result = _validate_doc_tree()
        print(json.dumps(result, ensure_ascii=False))
        return 0

    if args.action == "impact":
        print(json.dumps(compute_change_impact(args.paths), ensure_ascii=False))
        return 0

    if args.action in ("search", "retrieve-v2"):
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
