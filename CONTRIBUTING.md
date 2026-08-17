# Contributing to CoreBall

Contributions of all sizes are welcome — from typo fixes to new language parsers.

## Getting started

```bash
git clone https://github.com/francomano/coreball.git
cd coreball
python -m pip install -e ".[dev]"
```

## Development workflow

```bash
# Format
ruff format .

# Lint
ruff check .

# Type check
mypy src/coreball

# Test
pytest

# Build
python -m build
```

All four must pass before opening a PR.

## Project structure

```
src/coreball/
  scanner.py      — file discovery
  parsers.py      — language-specific extraction
  graph.py        — relationship inference
  selector.py     — scoring and token-budget packing
  renderers.py    — output formats (Markdown, JSON)
  cli.py          — command-line interface
  models.py       — public data models
  api.py          — public Python API
  tokens.py       — token estimation
tests/            — pytest tests
docs/             — internal documentation
```

## Adding a language parser

1. Edit `src/coreball/parsers.py`
2. Add a new `_<lang>_symbols()` function
3. Register it in the `parse_file()` dispatch
4. Add test files in `tests/`
5. Run `pytest` to verify

## Opening issues

- Use the provided issue templates (bug report, feature request)
- Label issues appropriately
- Include reproduction steps for bugs

## Pull requests

- Keep PRs focused on one change
- Run the full test suite before submitting
- Update documentation if adding features
- Reference related issues

## Code style

- Python 3.11+ with type hints
- `dataclasses` for models (no pydantic)
- No external runtime dependencies
- One function per concern
- Docstrings on all public functions
