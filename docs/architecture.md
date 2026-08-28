# Architecture

CoreBall v0.1 is a small Python package with a CLI, MCP server, HTTP API and public library.

## Components

- `scanner`: deterministic discovery with `DEFAULT_IGNORE_DIRS` + `.gitignore` support (stdlib `fnmatch` + `PurePosixPath`).
- `parsers`: language-specific extraction (Python AST, Go/Rust/PHP/JS/TS regex) with plugin hook.
- `plugins`: minimal analyzer registry (`register_analyzer`, `register_callable_analyzer`, `parse_with_plugins`).
- `models`: stable dataclass-based public data structures.
- `graph`: lightweight relationship inference between files.
- `selector`: task-aware scoring and token-budget packing with clear `max_tokens >=128` validation.
- `renderers`: Markdown and JSON output formats.
- `mcp_server`: stdio JSON-RPC 2.0 server exposing `pack`, `inspect`, `search_symbols`, `get_file_context`.
- `server`: stdlib `http.server` REST API (`/health`, `/api/pack`, `/api/inspect`, `/api/search`).
- `cli`: `argparse` CLI with `inspect`, `pack`, `mcp`, `serve`, `version`.

## Data flow

```text
repository -> scanner -> parsers (+plugins) -> RepositoryModel -> selector -> ContextPackage -> renderer
                                                                                    │
                                                                           mcp_server / server
```

## Design principles

- Deterministic output over opaque ranking.
- Zero runtime dependencies (stdlib only).
- Explainable selection reasons.
- Public API shaped around stable models (`inspect_repository`, `pack_repository` with `respect_gitignore`).
- Practical v0.1 functionality rather than placeholder research scaffolding.
- MCP + HTTP API as thin adapters over the same core — no duplication.

## Plugin interface

See `src/coreball/plugins.py` and `docs/design-decisions.md`. Registration is explicit, no entry-points magic.
Built-in parsers remain the fallback; a plugin returning `None` delegates to the next analyzer.
