# Changelog

All notable changes to CoreBall are documented in this file.

## 0.2.0 - 2026-08-29

### Added

- `.gitignore` pattern support (glob, directory, `!` negation, nested files) in `scanner` — fixes #2.
- Go, Rust and PHP language symbol extraction via stdlib regex — fixes #13, #14, #17.
- Minimal plugin interface `coreball.plugins` (`register_analyzer`, `register_callable_analyzer`, `parse_with_plugins`) — fixes #6.
- MCP server (`coreball mcp` / `python -m coreball.mcp_server`) with 4 tools (`pack`, `inspect`, `search_symbols`, `get_file_context`) — fixes #11.
- HTTP API server (`coreball serve` / `python -m coreball.server`) on stdlib `http.server` — `/health`, `/api/pack`, `/api/inspect`, `/api/search`.
- Claude Code & Cursor integration configs under `integrations/` with setup guide — fixes #16.
- Comprehensive test runner `scripts/test.sh` and quick `scripts/smoke_test.py`.

### Fixed

- Improved CLI error messages for invalid `--max-tokens` (mentions invalid value, minimum 128 and suggested fix) — fixes #1.

### Changed

- `inspect_repository` / `pack_repository` now accept `respect_gitignore` (default `True`).
- `scanner.LANGUAGE_BY_SUFFIX` extended with `.php`, `.rb`, `.cs`, `.cpp`, etc.
- CLI adds `--no-gitignore`, `--no-docs` propagation, and subcommands `mcp`, `serve`, `version`.

## 0.1.0 - 2026-07-27

### Added

- Initial CoreBall CLI with `inspect` and `pack` commands.
- Python AST symbol/import/call extraction.
- Conservative JavaScript/TypeScript symbol/import extraction.
- Task-aware context selector with graph-based relevance expansion.
- Markdown and JSON renderers.
- Public Python API.
- Tests, documentation, CI, issue templates and release metadata.
