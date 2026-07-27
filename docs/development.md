# Development guide

## Repository structure

```text
src/coreball/        package source
tests/               automated tests
docs/                engineering documentation
examples/            small runnable examples
.github/             GitHub workflows and templates
scripts/             maintenance and benchmark scripts
```

## Release checklist

1. Update `CHANGELOG.md`.
2. Run all quality checks.
3. Run CLI smoke tests.
4. Build the package.
5. Tag the release.

## Local commands

```bash
python -m pip install -e ".[dev]"
ruff format .
ruff check .
mypy src/coreball
pytest
coreball inspect . --format markdown
coreball pack . --task "explain the selector" --max-tokens 2048
python -m build
```
