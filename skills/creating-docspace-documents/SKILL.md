---
name: creating-docspace-documents
description: "Use when creating, rewriting, or adopting Markdown documents inside the docs/ tree. Prevents ad-hoc, unstructured documentation and keeps creation steps aligned with docspace-engine workflows."
---

# Creating Docspace Documents

## Overview

Documentation is not an afterthought; it is the blueprint. Creating random Markdown files without structure, frontmatter, or parent hierarchy is technical graffiti.

Never produce wild Markdown. Always obey the metadata contract.

## The Iron Law of Doc Creation

1. **NO ORPHANS:** Every non-root document MUST have a `parent` defined in its metadata.
2. **NO AD-HOC STRUCTURE:** Create documents with valid frontmatter and the correct parent chain.
3. **METADATA IS SCRIPTURE:** Every managed document must have `id`, `type`, `status`, and `maturity`.

## The Execution Workflow

If the user asks you to document a new module, architecture, or plan:

1. **Identify the Context:** Use `navigating-docspace-documents` to find where the new document belongs.
2. **Determine the Type:** Choose the closest supported type such as `project-index`, `architecture-node`, `reference`, or `plan`.
3. **Determine the Parent:** Find the exact `id` of the parent document.
4. **Create the Shell:**
   - Create the target markdown file manually.
   - Add minimal frontmatter: `id`, `type`, `status`, `maturity`, plus `parent` for every non-root document.
5. **Fill the Shell:** Populate the generated shell without destroying the YAML frontmatter.
6. **Refresh Searchability:**
   ```bash
   docspace-engine --workspace . status
   ```
7. **Validate Manually:**
   - Confirm the file is reachable from `docs/project-index.md` or its parent chain.
   - Confirm IDs and parents are spelled consistently.

## Parent Selection

- Put project entry documents under `project-index` only when they are genuinely top-level.
- Put architecture descriptions under an architecture node when possible.
- Put detailed implementation notes under the closest architecture or module parent.
- If adopting a legacy document and the exact parent is unclear, choose the narrowest plausible parent instead of leaving it unowned.

## Red Flags - REJECT THESE BEHAVIORS

- Creating a `.md` file directly without valid frontmatter and parent metadata.
- Leaving `parent` blank unless the file is literally the root `project-index`.
- Writing giant unstructured brain-dumps instead of a concise, navigable document.
- Changing an `id` later just because the title changed slightly.
