# Development guide

## Repository structure

```text
src/coreball/        package source
  scanner.py         file discovery + .gitignore (fnmatch, no deps)
  parsers.py         Python/Go/Rust/PHP/JS/TS extraction
  plugins.py         minimal analyzer registry
  mcp_server.py      stdio JSON-RPC 2.0 MCP (pack/inspect/search/get_file_context)
  server.py          http.server REST API (stdlib only)
tests/               automated tests
docs/                engineering documentation
examples/            small runnable examples
.github/             GitHub workflows and templates
scripts/             maintenance, benchmark and smoke scripts
integrations/        MCP configs for Claude Code / Cursor / Codex
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
ruff format --check .
ruff check .
mypy src/coreball
pytest
bash scripts/test.sh        # full suite: lint, types, tests, .gitignore, MCP, parsers
python scripts/smoke_test.py
coreball inspect . --format markdown
coreball pack . --task "explain the selector" --max-tokens 2048
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n' | coreball mcp
coreball serve --port 8765 &
curl http://127.0.0.1:8765/health; kill %1
python -m build
```

## Language support

- Python: `ast` (full fidelity)
- Go: `func`, `type struct/interface`, `import` blocks via regex
- Rust: `fn`, `struct`, `enum`, `trait`, `mod`, `use`
- PHP: `class`, `interface`, `trait`, `function`, `use`/`namespace`
- JS/TS: `import`/`require`, `function`/`class`/`const =>`
- Plugin API: `coreball.plugins.register_analyzer("go", my_parser)` — see `plugins.py`.

## .gitignore

`scanner.discover_files(..., respect_gitignore=True)` (default). Handles `*.ext`, `dir/`, `**/`, `!negation`, nested `.gitignore`. Disable with `--no-gitignore` or `respect_gitignore=False`.
