"""CoreBall HTTP API server — zero-dependency, stdlib only.

Provides a lightweight REST API around CoreBall's core functions.
Useful for CI, remote agents, and as a complement to the MCP server.

Endpoints:
    GET  /health              -> {"status": "ok", "version": "..."}
    POST /api/pack            -> pack_repository
    POST /api/inspect         -> inspect_repository
    POST /api/search          -> symbol search

Run:
    python -m coreball.server --port 8765
    coreball serve --port 8765

No external dependencies — uses http.server from stdlib.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import urlparse

from coreball.api import inspect_repository, pack_repository
from coreball.renderers import render_inspection, render_package

VERSION = "0.2.1"


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        # Less noisy: log to stderr with prefix
        import sys

        sys.stderr.write(f"coreball-api: {format % args}\n")

    def _json(self, code: int, payload: object) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._json(200, {"status": "ok", "version": VERSION})
            return
        if parsed.path == "/":
            self._json(
                200,
                {
                    "name": "coreball-api",
                    "version": VERSION,
                    "endpoints": ["/health", "/api/pack", "/api/inspect", "/api/search"],
                },
            )
            return
        self._json(404, {"error": f"Not found: {parsed.path}"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        data = self._read_json()
        if parsed.path == "/api/pack":
            try:
                repo = data["repository"]
                task = data["task"]
                max_tokens = int(data["max_tokens"])
                fmt = data.get("format", "json")
                package = pack_repository(repo, task=task, max_tokens=max_tokens)
                rendered = render_package(package, fmt=fmt)
                if fmt == "json":
                    self._json(200, json.loads(rendered))
                else:
                    self._json(
                        200, {"rendered": rendered, "estimated_tokens": package.estimated_tokens}
                    )
            except KeyError as exc:
                self._json(400, {"error": f"Missing field: {exc}"})
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
            except Exception as exc:  # noqa: BLE001
                self._json(500, {"error": str(exc)})
            return
        if parsed.path == "/api/inspect":
            try:
                repo = data["repository"]
                fmt = data.get("format", "json")
                model = inspect_repository(repo)
                rendered = render_inspection(model, fmt=fmt)
                if fmt == "json":
                    self._json(200, json.loads(rendered))
                else:
                    self._json(200, {"rendered": rendered})
            except KeyError as exc:
                self._json(400, {"error": f"Missing field: {exc}"})
            except Exception as exc:  # noqa: BLE001
                self._json(500, {"error": str(exc)})
            return
        if parsed.path == "/api/search":
            try:
                repo = data["repository"]
                query = data["query"].lower()
                limit = int(data.get("limit", 20))
                model = inspect_repository(repo)
                matches = []
                for file in model.files:
                    for sym in file.symbols:
                        if query in sym.name.lower() or query in sym.signature.lower():
                            matches.append(
                                {
                                    "name": sym.name,
                                    "kind": sym.kind,
                                    "file": sym.file_path,
                                    "signature": sym.signature,
                                    "line": sym.line_start,
                                }
                            )
                            if len(matches) >= limit:
                                break
                    if len(matches) >= limit:
                        break
                self._json(200, {"results": matches})
            except KeyError as exc:
                self._json(400, {"error": f"Missing field: {exc}"})
            except Exception as exc:  # noqa: BLE001
                self._json(500, {"error": str(exc)})
            return
        self._json(404, {"error": f"Not found: {parsed.path}"})

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Start the HTTP server (blocking)."""
    server = HTTPServer((host, port), _Handler)
    print(f"coreball API serving on http://{host}:{port}  (health: /health)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\ncoreball API stopped")
    finally:
        server.server_close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="coreball serve", description="Run CoreBall HTTP API server (stdlib only)"
    )
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_server(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
