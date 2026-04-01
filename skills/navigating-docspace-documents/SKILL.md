---
name: navigating-docspace-documents
description: "Use when you need semantic answers about project architecture or code locations, especially when entering a new worktree. Prevents guessing architecture by enforcing document-first reading via docspace-engine CLI with strict --workspace targeting and readiness checks before search."
---

# navigating-docspace-documents

## Description
This skill enforces strict discipline for querying project documentation (`docs/**/*.md`) and source code (`.py`, `.js`, etc.) using the Docspace Engine. It preserves the hierarchical top-down navigation approach starting from `docs/project-index.md` while integrating semantic search.

## Permissions Required
- Command Execution `docspace-engine`
- File Read Access to `docs/project-index.md` and related metadata.

## Execution Rules & Discipline

**Rule 1. Mandatory Status Check Before Searching**
You MUST NEVER run semantic search before checking readiness:
```bash
docspace-engine --workspace . status
```
- If state is `cold`, you MUST execute `index`.
- If state is `stale`, you MUST execute `index` (or `reindex` as recommended).
- If state is `hot`, you SHOULD proceed with search.

Do not trust semantic retrieval until the store is ready.

**Rule 2. Workspace Targeting (CRITICAL)**
Always pass `--workspace` accurately. Never assume a localized copy exists.
```bash
docspace-engine --workspace . status
```

**Rule 3. Top-Down Navigation Default**
Start at `docs/project-index.md`, then follow the smallest relevant branch in `docs/architecture/` or `docs/plans/`. Only fall back to semantic search when the tree does not answer the exact question.

**Rule 4. Semantic Search**
When specific class names, hidden architectural decisions, or precise implementation files are requested and cannot be found via filename or raw string searches, run:
```bash
docspace-engine --workspace . retrieve-v2 --query "<PRECISE_TECHNICAL_QUERY>" --budget normal
```

**Rule 5. Silent Absorption**
You MUST NOT output explanations of the search results to the User unless directly asked. Read the output silently to understand where the code lives, then proceed immediately to writing code or making edits.

**Rule 6. Actionable Queries**
Do not use vague queries. Use highly specific semantic queries.
- BAD: `--query "frontend"`
- GOOD: `--query "How does the ContextMenu popup handle z-index and Tailwind CSS conflicts?"`

## Workflow Checkpoints
1. Start at `docs/project-index.md`
2. Follow references to the most relevant `docs/architecture/` or `docs/plans/` node when possible
3. Run `docspace-engine --workspace . status`
4. If needed, run `docspace-engine --workspace . retrieve-v2 --query "<PRECISE_TECHNICAL_QUERY>"`
5. Verify hits against the actual file before answering or editing

## Handling the Unknown
If the documentation is missing, weak, or stale:
- **DO NOT GUESS.**
- Tell the user explicitly: `Checked docspace path: X -> Y; no sufficient doc found for module Z`.
- Ask whether we should document it first or proceed via code inspection.

## Current Repository Reality

- `docspace-engine` CLI is the active query entrypoint.
- Document creation and validation rely on frontmatter discipline plus manual review.

## Red Flags - STOP AND CORRECT
- Running semantic search without checking `status` first.
- Skipping `--workspace` and querying the wrong project scope.
- Ignoring cold-start or stale-index signals and then blaming search quality.
- Treating vector hits as facts instead of retrieval clues.
- Answering architectural questions from model memory instead of real docspace files.
