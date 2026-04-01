# docspace-vector

Use this tool to semantically search the entire project's docs and codebase (.MD, .PY, .JS, etc) using the docspace-engine.

## Commands
```bash
# Retrieve documentation context for a query
docspace-engine --workspace "/path/to/project" retrieve-v2 --query "<YOUR_QUERY>" --budget small

# Analyze impact of code changes
docspace-engine --workspace "/path/to/project" impact --paths src/sidebar.js
```

## Installation

Install docspace-engine in your project:
```bash
pip install -e /path/to/docspace-engine
```

Then use the `docspace-engine` command from anywhere.
