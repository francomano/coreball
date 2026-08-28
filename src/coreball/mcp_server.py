"""CoreBall MCP server — zero-dependency JSON-RPC 2.0 stdio server.

Exposes CoreBall as MCP tools so any MCP-compatible agent (Claude Code,
Cursor, Codex, Gemini CLI, Windsurf) can query context without re-scanning.

Tools exposed:
- pack — task-specific context package
- inspect — full semantic model
- search_symbols — fuzzy search across symbols
- get_file_context — context for a specific file

Usage:
    python -m coreball.mcp_server
    coreball mcp
    uvx coreball mcp   (after publish)

Compatible with Claude Code's `.mcp.json`:
    {
      "mcpServers": {
        "coreball": { "command": "python", "args": ["-m", "coreball.mcp_server"] }
      }
    }
"""

from __future__ import annotations

import json
import sys
from typing import Any

from coreball.api import inspect_repository, pack_repository
from coreball.renderers import render_package

SERVER_INFO = {"name": "coreball", "version": "0.2.1"}
PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "pack",
        "description": "Pack a task-specific context package within a token budget",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repository": {"type": "string", "description": "Path to repository root"},
                "task": {
                    "type": "string",
                    "description": "Task or question the context should support",
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum estimated token budget (min 128)",
                    "minimum": 128,
                },
                "format": {"type": "string", "enum": ["markdown", "json"], "default": "markdown"},
            },
            "required": ["repository", "task", "max_tokens"],
        },
    },
    {
        "name": "inspect",
        "description": "Return the full semantic model of a repository",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repository": {"type": "string", "description": "Path to repository root"},
                "format": {"type": "string", "enum": ["json", "markdown"], "default": "json"},
            },
            "required": ["repository"],
        },
    },
    {
        "name": "search_symbols",
        "description": "Fuzzy search across all symbols in a repository",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repository": {"type": "string", "description": "Path to repository root"},
                "query": {
                    "type": "string",
                    "description": "Search query (substring, case-insensitive)",
                },
                "limit": {"type": "integer", "description": "Max results", "default": 20},
            },
            "required": ["repository", "query"],
        },
    },
    {
        "name": "get_file_context",
        "description": "Get context excerpt for a specific file ranked for a task",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repository": {"type": "string", "description": "Path to repository root"},
                "file_path": {
                    "type": "string",
                    "description": "Relative file path inside repository",
                },
                "task": {"type": "string", "description": "Task to rank context for (optional)"},
                "max_tokens": {
                    "type": "integer",
                    "description": "Token budget if task provided",
                    "default": 800,
                },
            },
            "required": ["repository", "file_path"],
        },
    },
]


def _tool_pack(args: dict[str, Any]) -> dict[str, Any]:
    repo = args["repository"]
    task = args["task"]
    max_tokens = int(args["max_tokens"])
    fmt = args.get("format", "markdown")
    package = pack_repository(repo, task=task, max_tokens=max_tokens)
    rendered = render_package(package, fmt=fmt)
    # Also return structured data for JSON consumers
    return {
        "content": [{"type": "text", "text": rendered}],
        "structuredContent": {
            "task": package.task,
            "max_tokens": package.max_tokens,
            "estimated_tokens": package.estimated_tokens,
            "items": [
                {"path": i.path, "language": i.language, "score": i.score, "reason": i.reason}
                for i in package.items
            ],
            "omitted_files": list(package.omitted_files),
        },
    }


def _tool_inspect(args: dict[str, Any]) -> dict[str, Any]:
    repo = args["repository"]
    fmt = args.get("format", "json")
    model = inspect_repository(repo)
    if fmt == "json":
        from coreball.renderers import render_inspection

        rendered = render_inspection(model, fmt="json")
        data = json.loads(rendered)
        return {"content": [{"type": "text", "text": rendered}], "structuredContent": data}
    from coreball.renderers import render_inspection

    rendered = render_inspection(model, fmt="markdown")
    return {"content": [{"type": "text", "text": rendered}]}


def _tool_search_symbols(args: dict[str, Any]) -> dict[str, Any]:
    repo = args["repository"]
    query = args["query"].lower()
    limit = int(args.get("limit", 20))
    model = inspect_repository(repo)
    matches: list[dict[str, Any]] = []
    for file in model.files:
        for sym in file.symbols:
            if query in sym.name.lower() or query in sym.signature.lower():
                matches.append(
                    {
                        "name": sym.name,
                        "kind": sym.kind,
                        "file": sym.file_path,
                        "line": sym.line_start,
                        "signature": sym.signature,
                    }
                )
                if len(matches) >= limit:
                    break
        if len(matches) >= limit:
            break
    text = json.dumps(matches, indent=2)
    if not matches:
        text = f"No symbols matching '{args['query']}' found."
    return {"content": [{"type": "text", "text": text}], "structuredContent": {"results": matches}}


def _tool_get_file_context(args: dict[str, Any]) -> dict[str, Any]:
    repo = args["repository"]
    file_path = args["file_path"]
    task = args.get("task", "")
    max_tokens = int(args.get("max_tokens", 800))
    model = inspect_repository(repo)
    target = None
    for f in model.files:
        if f.path == file_path:
            target = f
            break
    if target is None:
        return {
            "content": [{"type": "text", "text": f"File not found: {file_path}"}],
            "isError": True,
        }
    if task:
        package = pack_repository(repo, task=task, max_tokens=max_tokens)
        for item in package.items:
            if item.path == file_path:
                return {
                    "content": [
                        {"type": "text", "text": f"## {item.path}\n{item.reason}\n\n{item.excerpt}"}
                    ],
                    "structuredContent": {
                        "path": item.path,
                        "score": item.score,
                        "excerpt": item.excerpt,
                    },
                }
        preview = target.text[:2000]
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"File {file_path} not selected for task '{task}'. Preview:\n{preview}",
                }
            ]
        }
    # No task: return raw excerpt
    preview = "\n".join(target.text.splitlines()[:80])
    return {
        "content": [
            {
                "type": "text",
                "text": f"## {target.path}\nLanguage: {target.language}\n\n```\n{preview}\n```",
            }
        ]
    }


_DISPATCH = {
    "pack": _tool_pack,
    "inspect": _tool_inspect,
    "search_symbols": _tool_search_symbols,
    "get_file_context": _tool_get_file_context,
}


def _handle_request(req: dict[str, Any]) -> dict[str, Any] | None:
    """Handle a single JSON-RPC request, return response or None for notifications."""
    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params") or {}

    def _resp(result: Any) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _err(code: int, message: str, data: Any = None) -> dict[str, Any]:
        err = {"code": code, "message": message}
        if data is not None:
            err["data"] = data
        return {"jsonrpc": "2.0", "id": req_id, "error": err}

    if method == "initialize":
        return _resp(
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
            }
        )
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return _resp({})
    if method == "tools/list":
        return _resp({"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        if name not in _DISPATCH:
            return _err(-32602, f"Unknown tool: {name}")
        try:
            result = _DISPATCH[name](args)
            return _resp(result)
        except Exception as exc:  # noqa: BLE001
            return _err(-32603, f"Tool '{name}' failed: {exc}")
    if method is None:
        return None
    return _err(-32601, f"Method not found: {method}")


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    """Run the MCP server on stdio."""
    # argv kept for CLI compatibility
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            resp: dict[str, Any] = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            }
            print(json.dumps(resp), flush=True)
            continue
        # Handle batch or single
        if isinstance(req, list):
            responses: list[dict[str, Any]] = []
            for single in req:
                r = _handle_request(single)
                if r is not None:
                    responses.append(r)
            if responses:
                print(json.dumps(responses), flush=True)
        else:
            resp2 = _handle_request(req)
            if resp2 is not None:
                print(json.dumps(resp2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
