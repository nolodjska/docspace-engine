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

## AI Team Integration

docspace-engine is designed for AI-driven development workflows. It serves as the documentation backbone for:

| Role | Tool | Usage |
|------|------|-------|
| **Batch Executor** | Codex | Executes implementation plans; uses `impact` to check what docs need updating |
| **Architect** | Claude Code | Writes plans and reviews code; uses `retrieve-v2` to fetch context before decisions |

**Typical workflow:**
1. Claude Code retrieves relevant docs via `retrieve-v2` before writing a plan
2. Codex executes the plan and runs `impact` to find affected documents
3. Both use `status` to verify docspace health before operations

## Development

```bash
# Run tests
pytest tests/unit -v

# Install in editable mode
pip install -e .
```

## License

Internal use only — extracted from the QI project.

---

## 中文说明

docspace-engine 是一个轻量级文档智能引擎，用于将代码变更与对应的设计文档、架构决策和知识库条目关联起来。

### 它能做什么

当你修改代码时，docspace-engine 会告诉你：

- 哪些文档受到你的变更影响
- 权威文档对这些组件的说明
- 鉴于最近的变更，文档是否仍然可信

### 快速开始

```bash
# 安装
pip install -e .

# 验证运行正常
docspace-engine --workspace /path/to/your/project status
# → {"state": "ready", "workspace": "/path/to/your/project"}
```

### 核心命令

**`status`** — 检查引擎是否能读取项目的文档树

```bash
docspace-engine --workspace ./my-project status
```

**`impact`** — 分析哪些文档受到文件变更的影响

```bash
docspace-engine --workspace ./my-project impact --paths src/sidebar.js src/routes.js
```

**`retrieve-v2`** — 检索任务或查询的文档上下文

```bash
# 快速查找
docspace-engine --workspace ./my-project retrieve-v2 --query "sidebar architecture" --budget small

# 深度调查
docspace-engine --workspace ./my-project retrieve-v2 --query "authentication flow" --budget deep
```

预算级别：`small`（1个推断文档）、`normal`（3个）、`deep`（6个）

### 文档格式

文档必须包含 YAML frontmatter：

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
```

### 工作原理

1. **文档发现** — 扫描 `docs/` 目录下带 YAML frontmatter 的 markdown 文件
2. **关系索引** — 通过 `implemented_by`、`tested_by`、`depends_on` 字段构建反向查找
3. **影响分析** — 通过关系索引将代码路径映射到文档
4. **信任层** — 当引用的代码变更时降低文档信任度

### AI 团队协作

docspace-engine 专为 AI 驱动开发流程设计，是以下角色的文档基础设施：

| 角色 | 工具 | 用途 |
|------|------|------|
| **批量执行** | Codex | 执行实现计划；使用 `impact` 检查哪些文档需要更新 |
| **架构师** | Claude Code | 编写计划和审阅代码；使用 `retrieve-v2` 在决策前获取上下文 |

**典型工作流：**
1. Claude Code 在编写计划前通过 `retrieve-v2` 检索相关文档
2. Codex 执行计划并运行 `impact` 查找受影响的文档
3. 双方在操作前使用 `status` 验证 docspace 状态
