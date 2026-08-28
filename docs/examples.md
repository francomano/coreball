# Examples

## Live demo — query this repository (Python client)

The canonical client demo is `examples/query_repository.py`. It queries **CoreBall itself** — no mocks — via all three surfaces (Python API, CLI, HTTP API):

```bash
# Run 3 demo tasks on the CoreBall repo itself
python examples/query_repository.py

# Single task
python examples/query_repository.py --task "where is .gitignore handling implemented" --max-tokens 1200

# Query any other repo
python examples/query_repository.py --repo /path/to/your/project --task "find the auth middleware"

# Also hit the HTTP API (needs `coreball serve` running)
coreball serve --port 8765 &
python examples/query_repository.py --http
```

What it does (see `examples/query_repository.py:37`):

```python
from coreball import inspect_repository, pack_repository

model = inspect_repository(".", respect_gitignore=True)
print(f"{len(model.files)} files, {model.symbol_count} symbols")

package = pack_repository(".", task="how does the MCP server work", max_tokens=1200)
for item in package.items:
    print(item.path, item.score, item.reason)
    print(item.excerpt[:400])
```

Sample output on CoreBall `main` (≈87 symbols, 45 files):

```
→ Selected 3 files, ~1200 tokens (budget 1200)
1. src/coreball/mcp_server.py  (score=74.34) — MCP stdio JSON-RPC
2. src/coreball/server.py      (score=74.49) — HTTP API http.server
3. scripts/benchmark.py        (score=31.10)
```

The same query via CLI (`examples/query_repository.py:81`):

```bash
coreball pack . --task "how does the MCP server work" --max-tokens 1200 --format json
curl -X POST http://127.0.0.1:8765/api/pack -H 'Content-Type: application/json' \
  -d '{"repository":".","task":"how does the MCP server work","max_tokens":1200}'
```

## Explain a subsystem

```bash
coreball pack . --task "explain how the command line interface works" --max-tokens 1800
```

## Prepare context for a bug fix

```bash
coreball pack . --task "fix incorrect authentication error handling" --max-tokens 2400 --format markdown
```

## Machine-readable context

```bash
coreball pack . --task "identify public API models" --max-tokens 1200 --format json
```
