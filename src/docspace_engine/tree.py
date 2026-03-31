from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

PROJECT_ROOT = "."
EXTRACT_FRONTMATTER: Callable[[str], dict] | None = None
EXTRACT_TITLE: Callable[[str], str] | None = None
EXTRACT_SUMMARY: Callable[[str], str] | None = None


def configure_tree_context(project_root: str, extract_frontmatter, extract_title, extract_summary):
    global PROJECT_ROOT, EXTRACT_FRONTMATTER, EXTRACT_TITLE, EXTRACT_SUMMARY
    PROJECT_ROOT = project_root
    EXTRACT_FRONTMATTER = extract_frontmatter
    EXTRACT_TITLE = extract_title
    EXTRACT_SUMMARY = extract_summary


def _iter_doc_files(project_root: str | None = None):
    root = Path(project_root or PROJECT_ROOT)
    docs_root = root / "docs"
    if not docs_root.exists():
        return []
    return sorted(str(path) for path in docs_root.rglob("*.md"))


def _get_doc_node(doc_id: str) -> dict | None:
    if EXTRACT_FRONTMATTER is None:
        return None
    for filepath in _iter_doc_files():
        meta = EXTRACT_FRONTMATTER(filepath) or {}
        if meta.get("id") != doc_id:
            continue
        return {
            "id": doc_id,
            "path": os.path.relpath(filepath, PROJECT_ROOT).replace("\\", "/"),
            "title": EXTRACT_TITLE(filepath) if EXTRACT_TITLE else doc_id,
            "summary": EXTRACT_SUMMARY(filepath) if EXTRACT_SUMMARY else "",
            **meta,
        }
    return None


def _get_children_of(doc_id: str) -> list[str]:
    children = []
    for filepath in _iter_doc_files():
        if EXTRACT_FRONTMATTER is None:
            continue
        meta = EXTRACT_FRONTMATTER(filepath) or {}
        if meta.get("parent") == doc_id and meta.get("id"):
            children.append(meta["id"])
    return sorted(children)


def get_ancestor_chain(doc_id: str) -> list[str]:
    chain = []
    current = _get_doc_node(doc_id)
    seen = set()
    while current and current.get("parent") and current["parent"] not in seen:
        parent_id = current["parent"]
        chain.append(parent_id)
        seen.add(parent_id)
        current = _get_doc_node(parent_id)
    return list(reversed(chain))


def get_children(doc_id: str) -> list[str]:
    return _get_children_of(doc_id)


def get_siblings(doc_id: str) -> list[str]:
    current = _get_doc_node(doc_id)
    if not current or not current.get("parent"):
        return []
    siblings = _get_children_of(current["parent"])
    return [item for item in siblings if item != doc_id]


def build_subtree_summary(doc_id: str, depth: int = 2) -> dict:
    current = _get_doc_node(doc_id)
    if not current:
        return {"current": None, "ancestors": [], "children": []}

    def _children(node_id: str, remaining: int):
        if remaining <= 0:
            return []
        result = []
        for child_id in _get_children_of(node_id):
            node = _get_doc_node(child_id)
            if not node:
                continue
            result.append({
                "id": child_id,
                "title": node.get("title", child_id),
                "children": _children(child_id, remaining - 1),
            })
        return result

    return {
        "current": current,
        "ancestors": [_get_doc_node(item) for item in get_ancestor_chain(doc_id)],
        "children": _children(doc_id, depth),
    }
