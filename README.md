# docspace-engine

Internal-first Docspace engine extracted from QI project.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Check engine status
docspace-engine --workspace /path/to/project status

# Compute change impact
docspace-engine --workspace /path/to/project impact --paths src/file.js

# Retrieve documentation context
docspace-engine --workspace /path/to/project retrieve-v2 --query "sidebar" --budget normal
```

## Commands

- `status` - Check if engine is ready
- `impact --paths <files>` - Analyze documentation impact of code changes
- `retrieve-v2 --query <text> [--budget small|normal|deep]` - Retrieve relevant documentation

## Requirements

- Python ≥ 3.11
