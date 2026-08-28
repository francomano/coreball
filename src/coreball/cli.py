"""CoreBall command line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NoReturn

from coreball.api import inspect_repository, pack_repository
from coreball.renderers import render_inspection, render_package


def _max_tokens_type(value: str) -> int:
    """Validate --max-tokens and produce a clear error message."""

    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid --max-tokens value '{value}': must be an integer >= 128. "
            f"Example: --max-tokens 512"
        ) from None
    if parsed < 128:
        raise argparse.ArgumentTypeError(
            f"Invalid --max-tokens value '{parsed}': must be at least 128. "
            f"Try: --max-tokens 512 (or higher)"
        )
    return parsed


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(
        prog="coreball",
        description="Compile a repository into compact semantic context for an LLM task.",
    )
    parser.add_argument("--version", action="version", version="coreball 0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_cmd = sub.add_parser("inspect", help="Build and print the repository semantic index.")
    inspect_cmd.add_argument("repository", type=Path)
    inspect_cmd.add_argument("--format", choices=["json", "markdown"], default="markdown")
    inspect_cmd.add_argument("--no-docs", action="store_true", help="Exclude Markdown files.")
    inspect_cmd.add_argument(
        "--no-gitignore", action="store_true", help="Do not respect .gitignore patterns."
    )
    inspect_cmd.add_argument(
        "--output", type=Path, help="Write output to a file instead of stdout."
    )

    pack_cmd = sub.add_parser("pack", help="Create a task-specific CoreBall context package.")
    pack_cmd.add_argument("repository", type=Path)
    pack_cmd.add_argument(
        "--task", required=True, help="Task or question the context should support."
    )
    pack_cmd.add_argument(
        "--max-tokens",
        type=_max_tokens_type,
        required=True,
        help="Maximum estimated token budget (minimum 128).",
    )
    pack_cmd.add_argument("--format", choices=["json", "markdown"], default="markdown")
    pack_cmd.add_argument("--no-docs", action="store_true", help="Exclude Markdown files.")
    pack_cmd.add_argument(
        "--no-gitignore", action="store_true", help="Do not respect .gitignore patterns."
    )
    pack_cmd.add_argument("--output", type=Path, help="Write output to a file instead of stdout.")

    mcp_cmd = sub.add_parser(
        "mcp", help="Run the MCP server on stdio (for Claude Code, Cursor, Codex)."
    )
    mcp_cmd.add_argument("--debug", action="store_true", help="Enable debug logging to stderr.")

    serve_cmd = sub.add_parser("serve", help="Run the HTTP API server.")
    serve_cmd.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    serve_cmd.add_argument("--port", type=int, default=8765, help="Port to bind (default: 8765)")

    sub.add_parser("version", help="Print version and exit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CoreBall CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    # Lightweight commands that don't need pack/inspect error handling
    if args.command == "mcp":
        from coreball.mcp_server import main as mcp_main

        return mcp_main([])
    if args.command == "serve":
        from coreball.server import run_server

        run_server(host=args.host, port=args.port)
        return 0
    if args.command == "version":
        print("coreball 0.1.0")
        return 0
    try:
        if args.command == "inspect":
            model = inspect_repository(
                args.repository,
                include_docs=not args.no_docs,
                respect_gitignore=not getattr(args, "no_gitignore", False),
            )
            output = render_inspection(model, fmt=args.format)
        elif args.command == "pack":
            package = pack_repository(
                args.repository,
                task=args.task,
                max_tokens=args.max_tokens,
                include_docs=not args.no_docs,
                respect_gitignore=not getattr(args, "no_gitignore", False),
            )
            output = render_package(package, fmt=args.format)
        else:
            _die(f"Unsupported command: {args.command}")
    except SystemExit:
        raise
    except ValueError as exc:
        # Enhanced error for invalid token budgets (includes the invalid value and minimum).
        print(f"coreball: error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - CLI must produce a concise user-facing error.
        print(f"coreball: error: {exc}", file=sys.stderr)
        return 2

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


def _die(message: str) -> NoReturn:
    raise SystemExit(message)


if __name__ == "__main__":
    raise SystemExit(main())
