# docspace-engine

A lightweight documentation intelligence engine that connects code changes to their corresponding design documents, architecture decisions, and knowledge base entries.

## What it does

When you modify code, docspace-engine tells you:

- Which documents are affected by your changes
- What the authoritative documentation says about those components
- Whether the documentation is still trustworthy given recent changes

## Quick Start

```bash
# Install
pip install -e .

# Verify it's working
docspace-engine --workspace /path/to/your/project status
# → {"state": "ready", "workspace": "/path/to/your/project"}
```

## Core Commands

### `status`
Check if the engine can read your project's documentation tree.

```bash
docspace-engine --workspace ./my-project status
```

### `impact`
Analyze which documents are affected by a set of file changes.

```bash
docspace-engine --workspace ./my-project impact --paths src/sidebar.js src/routes.js
```

Returns a structured report mapping changed files to their corresponding documentation, including trust degradation warnings.

### `retrieve-v2`
Retrieve documentation context for a task or query.

```bash
# Quick lookup
docspace-engine --workspace ./my-project retrieve-v2 --query "sidebar architecture" --budget small

# Deep investigation
docspace-engine --workspace ./my-project retrieve-v2 --query "authentication flow" --budget deep --changed-paths src/auth.js
```

Budget levels:
- `small` — 1 inferred document
- `normal` — 3 inferred documents  
- `deep` — 6 inferred documents

## How it works

1. **Document Discovery** — Scans `docs/` for markdown files with YAML frontmatter
2. **Relation Indexing** — Builds reverse lookup from `implemented_by`, `tested_by`, `depends_on` fields
3. **Impact Analysis** — Maps code paths to documents via the relation index
4. **Trust Layer** — Degrades document trust when referenced code changes

## Document Format

Documents must include frontmatter:

```markdown
---
id: sidebar-arch
type: architecture
status: active
maturity: stable
parent: project-index
implemented_by:
  - src/components/sidebar.js
tested_by:
  - tests/sidebar.test.js
---

# Sidebar Architecture

Content here...
```

## Requirements

- Python ≥ 3.11

## Development

```bash
# Run tests
pytest tests/unit -v

# Install in editable mode
pip install -e .
```

## License

Internal use only — extracted from the QI project.
