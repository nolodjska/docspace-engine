---
name: maintaining-docspace-documents
description: "Use when code or architecture changes require updating existing Docspace documents. Ensures the documentation tree remains trustworthy."
---

# Maintaining Docspace Documents

## Overview

Stale documentation is worse than no documentation - it is a lie that wastes the next developer's time. When you change code, you MUST update the corresponding leaf document, then trace the impact up the parent chain.

## The Iron Law of Maintenance

**Update the leaf first, then inspect the parent.** Never assume a parent document is still accurate after a child changes.

## Maintenance Workflow

1. **Locate the Target:** Use `navigating-docspace-documents` principles to find the exact document corresponding to the code you changed.
2. **Update the Leaf:** Correct facts, scope, examples, and metadata.
3. **Verify the Status:**
   - If the change is a workaround or temporary bridge, demote `maturity` to `temporary`.
   - If it is proven and reusable, promote `maturity` to `stable`.
4. **Walk the Chain:** Open the document's `parent`. If the parent summary no longer matches reality, either fix it or mark it clearly as stale.
5. **Refresh Searchability:**
   ```bash
   docspace-engine --workspace . status
   ```
6. **Validate Against Current Reality:**
   - Manually check frontmatter, parent linkage, and rediscoverability.

## How to Handle Stale Parents

- If the parent only needs a short summary refresh, update it immediately.
- If the parent is partly outdated but a full rewrite is not worth it yet, lower confidence explicitly. A practical default is to set `status: draft` until the parent catches up.
- If the parent remains valid at its own abstraction level, leave it alone. Do not copy all child details upward.

## Legacy Adoption

If you encounter an old Markdown file in `docs/` or `_archive/` that lacks YAML frontmatter:
1. Do not just start editing the text.
2. Add the minimal docspace metadata contract first: `id`, `type`, `status`, `maturity`, and `parent`.
3. Only then clean the content.

## Red Flags - REJECT THESE BEHAVIORS

- Updating code but ignoring the docs.
- Updating a child document while leaving the parent claiming the old architecture.
- Marking a rushed or unpolished feature as `stable`.
- Running bulk edits across docs without refreshing the docspace index.
