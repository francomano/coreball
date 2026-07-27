# Contributing

Thank you for considering a contribution to CoreBall.

## Development setup

```bash
git clone https://github.com/coreball/coreball.git
cd coreball
python -m pip install -e ".[dev]"
```

## Quality checks

Run all checks before opening a pull request:

```bash
ruff format --check .
ruff check .
mypy src/coreball
pytest
python -m build
```

## Contribution guidelines

- Keep dependencies minimal.
- Prefer readable code over clever abstractions.
- Document public APIs and design decisions.
- Add tests for every behavior change.
- Avoid placeholder implementations and TODO-driven architecture.

## Pull requests

A good pull request includes:

- A clear problem statement.
- A focused implementation.
- Tests covering the change.
- Documentation updates when behavior changes.
