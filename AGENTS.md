# AGENTS.md — CoreBall

## What is CoreBall

CoreBall is a semantic context compiler for LLM coding agents. It analyzes a codebase, ranks files by relevance to a task, and emits a compact context package that fits a token budget. Zero dependencies, deterministic, pure Python stdlib.

## Repository structure

```
src/coreball/       # Main package
  __init__.py       # Public API: inspect_repository, pack_repository
  api.py            # Core functions
  cli.py            # CLI entry point (argparse)
  models.py         # Dataclasses: RepositoryModel, ContextPackage, Symbol, etc.
  scanner.py        # File discovery with ignore rules
  parsers.py        # Language-specific extraction (Python AST, JS/TS regex)
  graph.py          # Lightweight relationship inference
  selector.py       # Task-aware scoring and token-budget packing
  tokens.py         # Token estimation
  renderers.py      # Markdown and JSON output
tests/              # pytest tests
docs/               # Internal documentation
examples/           # Example scripts
```

## Build and test commands

```bash
python -m pip install -e ".[dev]"
ruff format --check .
ruff check .
mypy src/coreball
pytest
python -m build
```

## Code conventions

- Python 3.11+, type hints everywhere
- `dataclasses` for models (no pydantic, no runtime deps)
- `ruff` for formatting and linting
- `mypy --strict` for type checking
- No external runtime dependencies — only stdlib
- Docstrings on all public functions
- One function per concern, small focused modules

## Key design principles

1. **Zero dependencies** — never add a runtime dependency
2. **Deterministic** — same input must always produce same output
3. **Explainable** — every file selection includes a reason
4. **Budget-aware** — token limits are hard constraints
5. **Auditable** — all logic is simple enough to read and verify

## Common tasks

- **Add a language parser**: edit `src/coreball/parsers.py`, add extraction logic, add tests in `tests/`
- **Improve ranking**: edit `src/coreball/selector.py` scoring functions
- **Add output format**: edit `src/coreball/renderers.py`
- **CLI changes**: edit `src/coreball/cli.py`
