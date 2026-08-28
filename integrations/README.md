# Integrations

CoreBall ships a zero-dependency MCP server and HTTP API so any agent can use it as a context provider.

## MCP (Claude Code, Cursor, Codex, Windsurf, Gemini CLI)

The MCP server runs on stdio JSON-RPC 2.0 and exposes 4 tools: `pack`, `inspect`, `search_symbols`, `get_file_context`.

**Claude Code**

Add to `.mcp.json` (or global `~/.claude.json`):

```json
{
  "mcpServers": {
    "coreball": { "command": "coreball", "args": ["mcp"] }
  }
}
```

Or with `python -m`:

```json
{ "mcpServers": { "coreball": { "command": "python", "args": ["-m", "coreball.mcp_server"] } } }
```

Restart Claude Code and verify with `/mcp` then `coreball__pack`.

**Cursor**

Settings → Features → MCP → Add Server:

- Command: `coreball`
- Args: `mcp`

See `integrations/cursor.json` for a copy-paste sample.

**Codex / Windsurf**

Same MCP config — any MCP-compatible client works. Point it at `coreball mcp`.

**Smoke test the MCP server**

```bash
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n' | coreball mcp
printf '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n' | coreball mcp
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"pack","arguments":{"repository":".","task":"explain CLI","max_tokens":800}}}' | coreball mcp
```

## HTTP API

```bash
coreball serve --port 8765
# or
python -m coreball.server --port 8765
curl http://127.0.0.1:8765/health
curl -X POST http://127.0.0.1:8765/api/pack -H 'Content-Type: application/json' \
  -d '{"repository":".","task":"explain selector","max_tokens":800}'
```

Stdlib only — no FastAPI/Uvicorn needed.
