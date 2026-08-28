#!/usr/bin/env python3
# ruff: noqa: E501
"""Query this repository with CoreBall — live client demo.

This script *queries CoreBall itself* so you can see token-efficient
context compilation on a real codebase without any mocks.

It demonstrates the three supported surfaces:
  1. Python API  — `inspect_repository` / `pack_repository`
  2. CLI        — `coreball pack ...` via subprocess
  3. HTTP API   — `coreball serve` + stdlib http.client

Usage:
  python examples/query_repository.py                  # runs 3 demo tasks on .
  python examples/query_repository.py --task "how does .gitignore work" --max-tokens 1200
  python examples/query_repository.py --repo /path/to/other/repo --task "explain auth"

Zero dependencies beyond CoreBall (stdlib only).
"""

from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import sys
import textwrap
from pathlib import Path

# Ensure `src/` is on sys.path when running from a checkout without install
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from coreball import (  # type: ignore[import-untyped]  # noqa: E402
    inspect_repository,
    pack_repository,
)

DEMO_TASKS: list[tuple[str, int]] = [
    ("explain how the selector ranks files", 1200),
    ("how does the MCP server work", 1200),
    ("where is .gitignore handling implemented", 1000),
]


def _header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def run_api_demo(repo: Path, task: str, max_tokens: int) -> None:
    """Run a single task via the Python API and pretty-print results."""
    _header(f"API · task={task!r}  budget={max_tokens}")
    model = inspect_repository(repo, include_docs=True, respect_gitignore=True)
    print(f"Repository: {repo}  —  {len(model.files)} files, {model.symbol_count} symbols")

    package = pack_repository(repo, task=task, max_tokens=max_tokens)
    print(
        f"→ Selected {len(package.items)} files, "
        f"~{package.estimated_tokens} tokens (budget {package.max_tokens})"
    )
    print(f"  Omitted: {len(package.omitted_files)} files")
    print(f"  Summary: {package.summary}\n")

    for i, item in enumerate(package.items, 1):
        print(f"{i}. {item.path}  (score={item.score}, lang={item.language})")
        print(f"   reason: {item.reason[:120]}")
        # Show first 4 non-empty excerpt lines
        excerpt_preview = "\n".join(line for line in item.excerpt.splitlines() if line.strip())[
            :500
        ]
        # Indent preview
        indented = textwrap.indent(
            excerpt_preview[:400] + ("…" if len(excerpt_preview) > 400 else ""), "   | "
        )
        print(indented)
        print()
        if i >= 5 and len(package.items) > 5:
            print(f"   … and {len(package.items) - 5} more files (truncated)")
            break


def run_cli_demo(repo: Path, task: str, max_tokens: int) -> None:
    """Smoke the CLI as a client would in CI."""
    _header("CLI · coreball pack --format json")
    cmd = [
        sys.executable,
        "-m",
        "coreball.cli",
        "pack",
        str(repo),
        "--task",
        task,
        "--max-tokens",
        str(max_tokens),
        "--format",
        "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"CLI failed ({result.returncode}): {result.stderr}", file=sys.stderr)
        return
    data = json.loads(result.stdout)
    print(f"CLI returned {len(data['items'])} items, estimated_tokens={data['estimated_tokens']}")
    for it in data["items"][:3]:
        print(f"  - {it['path']}  score={it['score']}")


def run_http_demo(repo: Path, task: str, max_tokens: int) -> None:
    """Optional demo of the HTTP API using only stdlib http.client."""
    _header("HTTP API · POST /api/pack (requires `coreball serve`)")
    print("Tip: in another terminal run  `coreball serve --port 8765`  then re-run this demo.")
    import http.client

    conn = http.client.HTTPConnection("127.0.0.1", 8765, timeout=1.5)
    payload = json.dumps(
        {"repository": str(repo), "task": task, "max_tokens": max_tokens, "format": "json"}
    )
    try:
        conn.request(
            "POST", "/api/pack", body=payload, headers={"Content-Type": "application/json"}
        )
        resp = conn.getresponse()
        body = resp.read().decode()
        if resp.status != 200:
            print(f"  (server not running or error {resp.status}: {body[:200]})")
            return
        data = json.loads(body)
        print(f"  HTTP API returned {len(data.get('items', []))} items")
    except (ConnectionRefusedError, OSError, TimeoutError) as exc:
        print(f"  (HTTP API not reachable: {exc} — start `coreball serve` to test)")
    finally:
        with contextlib.suppress(Exception):
            conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Query the CoreBall repository itself — live demo."
    )
    parser.add_argument(
        "--repo", type=Path, default=ROOT, help="Repository to query (default: CoreBall itself)"
    )
    parser.add_argument(
        "--task", type=str, default="", help="Single task to run (default: 3 demo tasks)"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=1200, help="Token budget for single-task mode"
    )
    parser.add_argument(
        "--http", action="store_true", help="Also try the HTTP API demo (needs coreball serve)"
    )
    parser.add_argument("--no-cli", action="store_true", help="Skip CLI demo")
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    if not repo.is_dir():
        print(f"error: repo not found: {repo}", file=sys.stderr)
        return 2

    # Quick sanity: show the semantic index head
    _header("Inspect — semantic index")
    model = inspect_repository(repo)
    print(f"Root: {model.root}")
    print(f"Files: {len(model.files)}   Symbols: {model.symbol_count}")
    top_langs: dict[str, int] = {}
    for f in model.files:
        top_langs[f.language] = top_langs.get(f.language, 0) + 1
    print("By language:", ", ".join(f"{k}={v}" for k, v in sorted(top_langs.items())))

    tasks = [(args.task, args.max_tokens)] if args.task else DEMO_TASKS

    for task, budget in tasks:
        run_api_demo(repo, task, budget)
        if not args.no_cli and task == tasks[0][0]:
            run_cli_demo(repo, task, budget)
            if args.http:
                run_http_demo(repo, task, budget)

    _header("Next steps")
    print(
        textwrap.dedent(
            f"""
            Try your own question on this repo:
              python examples/query_repository.py --task "explain how the plugin system works" --max-tokens 1500

            Or run the CLI directly:
              coreball pack {repo} --task "where is token estimation done" --max-tokens 800 --format markdown

            Or query any other repo:
              python examples/query_repository.py --repo /path/to/your/project --task "find the auth middleware"

            JSON output for LLM pipelines:
              coreball pack {repo} --task "summarize the MCP server" --max-tokens 1200 --format json --output context.json
            """
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
