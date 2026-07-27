# Contributing to CoreBall

See [docs/contributing.md](docs/contributing.md) for the full development guide.

Before opening a pull request, run:

```bash
ruff format --check .
ruff check .
mypy src/coreball
pytest
python -m build
```
