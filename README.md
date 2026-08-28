# CoreBall

Semantic context compiler for LLM coding agents. Zero dependencies, deterministic, token-efficient — ranks every file by relevance to a task and packs the smallest useful context.

## Install

```bash
pip install coreball
# dev
pip install -e ".[dev]"
```

## Usage

**CLI**
```bash
coreball inspect . --format markdown
coreball pack . --task "explain how authentication works" --max-tokens 2048
coreball pack . --task "find the CLI entry point" --max-tokens 1200 --format json --output context.json
```

**Python API**
```python
from coreball import inspect_repository, pack_repository

model = inspect_repository(".")
package = pack_repository(".", task="explain how the CLI builds a context package", max_tokens=2048)
print(f"{len(package.items)} files, ~{package.estimated_tokens} tokens")
```

**MCP (Claude Code / Cursor / Codex)**
```bash
coreball mcp
# .mcp.json
{ "mcpServers": { "coreball": { "command": "coreball", "args": ["mcp"] } } }
```
Tools: `pack`, `inspect`, `search_symbols`, `get_file_context`.

**HTTP API**
```bash
coreball serve --port 8765
curl -X POST http://127.0.0.1:8765/api/pack -H 'Content-Type: application/json' \
  -d '{"repository":".","task":"explain selector","max_tokens":800}'
# GET /health
```

## Example

Live demo che interroga CoreBall stesso (API + CLI + HTTP):

```bash
python examples/query_repository.py
python examples/query_repository.py --task "where is .gitignore handling implemented" --max-tokens 1200 --http
python examples/query_repository.py --repo /path/to/your/project --task "find the auth middleware"
```

Vedi [`examples/query_repository.py`](examples/query_repository.py).

## License

MIT — [LICENSE](LICENSE)
