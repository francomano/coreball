# CoreBall

<p align="center">
  <a href="https://github.com/francomano/coreball/actions"><img src="https://img.shields.io/github/actions/workflow/status/francomano/coreball/ci.yml?branch=main&label=CI&logo=github&style=flat-square" alt="CI"></a>
  <a href="https://pypi.org/project/coreball/"><img src="https://img.shields.io/pypi/v/coreball?logo=pypi&style=flat-square" alt="PyPI"></a>
  <a href="https://pypi.org/project/coreball/"><img src="https://img.shields.io/pypi/pyversions/coreball?logo=python&style=flat-square" alt="Python versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License"></a>
  <a href="https://github.com/francomano/coreball/issues"><img src="https://img.shields.io/github/issues/francomano/coreball?style=flat-square" alt="Issues"></a>
  <a href="https://github.com/francomano/coreball/stargazers"><img src="https://img.shields.io/github/stars/francomano/coreball?style=flat-square" alt="Stars"></a>
</p>

<p align="center">
  <strong>Semantic context compiler for LLM coding agents.</strong><br>
  Zero dependencies. Deterministic. Token-efficient.<br>
  Compile your codebase into the smallest useful context for any task.
</p>

---

**Stop wasting tokens on irrelevant code.** CoreBall analyzes your repository, ranks every file by relevance to a specific task, and emits a compact context package that fits your LLM's context window — no RAG, no embeddings, no bloat.

While other tools re-read your entire codebase on every query, CoreBall pre-compiles a semantic map once and reuses it. The result: **60-90% fewer tokens**, deterministic output, and explainable selection.

## Quick Start

```bash
pip install coreball
```

**Compile context for a task:**

```bash
coreball pack . --task "explain how authentication works" --max-tokens 2048
```

**Inspect the full semantic index:**

```bash
coreball inspect . --format markdown
```

**Pipe into your LLM workflow:**

```bash
coreball pack . --task "find the CLI entry point" --max-tokens 1200 --format json --output context.json
```

## Python API

```python
from coreball import inspect_repository, pack_repository

# Build semantic model (reuse across tasks)
model = inspect_repository(".")

# Compile task-specific context
package = pack_repository(
    ".",
    task="explain how the CLI builds a context package",
    max_tokens=2048,
)

print(f"Selected {len(package.items)} files, ~{package.estimated_tokens} tokens")
```

## Why CoreBall

| | Whole-file prompting | RAG / embeddings | **CoreBall** |
|---|---|---|---|
| **Token cost** | Sends everything | Chunks loosely | **Task-ranked, budget-capped** |
| **Determinism** | N/A | No (embedding drift) | **Yes — same input, same output** |
| **Relationships** | None | Weak | **Symbol + import graph** |
| **Explainability** | None | Black box | **Every selection traced** |
| **Dependencies** | None | Heavy | **Zero** (pure stdlib) |
| **Setup** | None | Vector DB + embeddings | **`pip install coreball`** |

## How It Works

```
repository ──> scanner ──> parsers ──> semantic model ──> task scorer ──> graph expansion ──> context packager ──> MCP / HTTP API
                  │              │              │                │                │
                  │              │              │                │                └── relevance boost through
                  │              │              │                └── lexical + symbol + doc scoring
                  │              │              └── files, symbols, imports, call names
                  │              └── Python AST, Go/Rust/PHP regex, JS/TS regex, Markdown
                  └── skip .git, node_modules, __pycache__, + .gitignore
```

1. **Scan** — discover source files, skip build/dependency dirs + `.gitignore`
2. **Parse** — extract symbols/imports/calls (Python AST, Go/Rust/PHP + JS/TS regex)
3. **Rank** — score every file against the task using lexical, symbol, and doc matches
4. **Expand** — boost files that import or call top-ranked files
5. **Pack** — fit the best excerpts within the token budget
6. **Render** — output Markdown or JSON
7. **Serve** — expose via MCP stdio or HTTP API for agents

## Features

- **Zero dependencies** — pure Python standard library. Nothing to install.
- **Deterministic** — same input always produces the same output
- **Language-aware** — Python (AST), Go, Rust, PHP, JavaScript/TypeScript, Markdown, config files
- **.gitignore-aware** — respects `.gitignore` patterns out of the box (`--no-gitignore` to disable)
- **MCP server** — stdio JSON-RPC 2.0 for Claude Code / Cursor / Codex / Windsurf
- **HTTP API** — `coreball serve` — `http.server` stdlib only
- **Plugin interface** — register custom analyzers without forking
- **Task-scoped** — scores and selects only what matters for your question
- **Token-budget control** — clear error for `--max-tokens < 128` with suggestion
- **Dual output** — Markdown for humans, JSON for pipelines
- **Explainable** — every file includes a reason for inclusion
- **Graph-based expansion** — imports and call relationships boost relevance

## Use Cases

- **LLM context optimization** — feed your coding agent only what it needs
- **Code review context** — compile relevant files for a diff or PR
- **Documentation generation** — extract the core modules for any subsystem
- **Onboarding** — generate a compact map of a new codebase
- **CI/CD pipelines** — automate context selection for AI-assisted workflows

## Comparison with Similar Tools

CoreBall occupies a unique niche: **pure Python, zero dependencies, deterministic context compilation**.

| Tool | Language | Approach | Dependencies | MCP |
|---|---|---|---|---|
| **CoreBall** | Python | Semantic compiler | Zero | Yes |
| codegraph | TypeScript/Rust | Knowledge graph | Heavy | Yes |
| understand-Anything | TypeScript | Multi-agent graph | LLM + heavy | Yes |
| graphsift | Python | BM25 + AST graph | Heavy | Yes |
| context-router | Python | Ranked context packs | Heavy | Yes |

CoreBall trades runtime sophistication for simplicity and determinism. No databases, no embeddings, no LLM calls — just a clean semantic compiler you can audit, test, and extend.

## MCP Server & HTTP API

**MCP (Claude Code, Cursor, Codex):**

```bash
coreball mcp
# or
python -m coreball.mcp_server
```

Add to `.mcp.json`:

```json
{ "mcpServers": { "coreball": { "command": "coreball", "args": ["mcp"] } } }
```

Tools exposed: `pack`, `inspect`, `search_symbols`, `get_file_context`. See [integrations/README.md](integrations/README.md).

**HTTP API:**

```bash
coreball serve --port 8765
curl -X POST http://127.0.0.1:8765/api/pack -H 'Content-Type: application/json' \
  -d '{"repository":".","task":"explain selector","max_tokens":800}'
```

Zero deps — `http.server` stdlib only. Health at `GET /health`.

## Limitations

- Token counts are estimates, not tokenizer-specific
- Python/Go/Rust/PHP support strongest; JS/TS uses conservative regex extraction
- Relationship inference is intentionally shallow in v0.1
- No language server or build system integration yet

## Development

```bash
python -m pip install -e ".[dev]"
ruff format --check .
ruff check .
mypy src/coreball
pytest
bash scripts/test.sh        # lint + types + tests + smoke (MCP, .gitignore, parsers)
python scripts/smoke_test.py
python -m build
```

Quick smoke:

```bash
coreball inspect . --format markdown
coreball pack . --task "explain the selector" --max-tokens 2048
printf '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}\n' | coreball mcp
coreball serve --port 8765 &
curl http://127.0.0.1:8765/health
```

## Contributing

Contributions of all sizes are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

**High-impact areas:**
- Add language parsers (Go, Rust, Java, C#, PHP)
- Implement MCP server for Claude Code / Cursor / Codex integration
- Improve the relationship graph and ranking algorithm
- Add tree-sitter parsing for more precise AST extraction
- Write benchmarks against real-world repositories
- Documentation and examples

## License

CoreBall is released under the [MIT License](LICENSE).
