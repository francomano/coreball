"""CoreBall command line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import NoReturn

from coreball.api import inspect_repository, pack_repository
from coreball.renderers import render_inspection, render_package


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
        "--output", type=Path, help="Write output to a file instead of stdout."
    )

    pack_cmd = sub.add_parser("pack", help="Create a task-specific CoreBall context package.")
    pack_cmd.add_argument("repository", type=Path)
    pack_cmd.add_argument(
        "--task", required=True, help="Task or question the context should support."
    )
    pack_cmd.add_argument(
        "--max-tokens", type=int, required=True, help="Maximum estimated token budget."
    )
    pack_cmd.add_argument("--format", choices=["json", "markdown"], default="markdown")
    pack_cmd.add_argument("--no-docs", action="store_true", help="Exclude Markdown files.")
    pack_cmd.add_argument("--output", type=Path, help="Write output to a file instead of stdout.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CoreBall CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            model = inspect_repository(args.repository, include_docs=not args.no_docs)
            output = render_inspection(model, fmt=args.format)
        elif args.command == "pack":
            package = pack_repository(
                args.repository,
                task=args.task,
                max_tokens=args.max_tokens,
                include_docs=not args.no_docs,
            )
            output = render_package(package, fmt=args.format)
        else:
            _die(f"Unsupported command: {args.command}")
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
