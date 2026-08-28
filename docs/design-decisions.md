# Design decisions

## Python first

Python provides a mature standard-library AST and is common in LLM tooling. CoreBall starts there while leaving room for language-server-backed analyzers later.

## No runtime dependencies

The v0.1 CLI and library depend only on the Python standard library. This keeps installation simple and avoids dependency churn for early adopters.

## Dataclasses instead of validation frameworks

CoreBall's internal models are small and stable. Dataclasses make the public API readable without introducing a schema dependency.

## Conservative token estimation

Tokenizer-specific counting would require model-specific dependencies. v0.1 uses a deterministic lexical estimate with a conservative multiplier.

## Regex JavaScript/TypeScript parsing

The JavaScript/TypeScript parser is deliberately conservative. It extracts common imports, functions, classes and arrow-function exports without pretending to be a full compiler.

## Regex Go/Rust/PHP parsing

Same philosophy: zero deps, no tree-sitter yet. Go/Rust/PHP use multiline regex for `func`/`fn`/`function`, `struct`/`class`, `import`/`use`. Accurate enough for ranking and graph expansion; a future tree-sitter backend can be added behind the plugin interface without breaking the API.

## Plugin interface — why minimal

`coreball.plugins` is deliberately tiny: a `Callable[[Path, Path], SourceFile | None]` plus a dict registry. No entry-points auto-discovery, no class hierarchy. This avoids overengineering and keeps determinism. Built-ins stay the fallback; a plugin returning `None` delegates to the next one. See `src/coreball/plugins.py`.

## .gitignore without dependencies

No `pathspec`/`gitignore-parser` at runtime. CoreBall implements a small `fnmatch` + `PurePosixPath.match` based matcher covering `*`, `**`, `/`, `!` negation and nested `.gitignore`. Good enough for the 99% case; heavy repos can still use `--no-gitignore`.

## MCP + HTTP API as adapters

Both servers are thin adapters over `coreball.api` — no duplicated logic. MCP uses stdio JSON-RPC 2.0, HTTP uses `http.server`. No FastAPI/Uvicorn/Starlette to preserve the zero-dependency promise.

## Markdown and JSON output

Markdown is immediately useful for LLM prompts. JSON is useful for automation and future integrations.
