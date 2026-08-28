#!/usr/bin/env python3
"""Quick smoke test for CoreBall — runs in <2s, zero deps beyond stdlib + coreball."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, **kw)


def check_inspect(tmp: Path) -> None:
    r = run(
        [sys.executable, "-m", "coreball.cli", "inspect", str(tmp), "--format", "json"], check=True
    )
    data = json.loads(r.stdout)
    assert data["symbol_count"] >= 3, data
    print(f"  inspect OK ({data['file_count']} files, {data['symbol_count']} symbols)")


def check_pack(tmp: Path) -> None:
    r = run(
        [
            sys.executable,
            "-m",
            "coreball.cli",
            "pack",
            str(tmp),
            "--task",
            "fix authentication",
            "--max-tokens",
            "900",
        ],
        check=True,
    )
    assert "CoreBall Context Package" in r.stdout
    print("  pack OK")


def check_gitignore() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".gitignore").write_text("*.ignored\nbuild/\n", encoding="utf-8")
        (root / "a.py").write_text("x=1\n", encoding="utf-8")
        (root / "b.ignored").write_text("x\n", encoding="utf-8")
        (root / "build").mkdir()
        (root / "build" / "c.py").write_text("y=1\n", encoding="utf-8")
        from coreball.scanner import discover_files

        files = discover_files(root, respect_gitignore=True)
        names = {p.name for p in files}
        assert "a.py" in names
        assert "b.ignored" not in names
        assert "c.py" not in names
    print("  .gitignore OK")


def check_cli_error() -> None:
    r = run(
        [sys.executable, "-m", "coreball.cli", "pack", ".", "--task", "x", "--max-tokens", "10"]
    )
    assert r.returncode != 0
    assert "at least 128" in r.stderr or "at least 128" in r.stdout
    print("  CLI error message OK")


def check_mcp() -> None:
    inp = (
        '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n'
        '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n'
    )
    r = run([sys.executable, "-m", "coreball.mcp_server"], input=inp)
    assert '"tools"' in r.stdout, r.stdout
    print("  MCP OK")


def check_parsers() -> None:
    from coreball.parsers import _parse_go, _parse_php, _parse_rust

    go = _parse_go(
        "a.go", "go", 100, 'package main\nimport "fmt"\nfunc Hello(){}\ntype Foo struct{}'
    )
    assert any(s.name == "Hello" for s in go.symbols)
    rust = _parse_rust("a.rs", "rust", 100, "use std::io;\nfn hello(){}\nstruct Foo;")
    assert any(s.name == "hello" for s in rust.symbols)
    php = _parse_php("a.php", "php", 100, "<?php\nuse Foo\\Bar;\nclass Baz{}\nfunction hello(){}")
    assert any(s.name == "Baz" for s in php.symbols)
    print("  Go/Rust/PHP parsers OK")


def main() -> int:
    print("CoreBall smoke_test.py")
    # Build a tiny repo like tests
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
        pkg = tmp / "demo"
        pkg.mkdir()
        (pkg / "auth.py").write_text(
            'class User:\n    pass\ndef authenticate(t): return t=="x"\n', encoding="utf-8"
        )
        (pkg / "api.py").write_text(
            "from demo.auth import authenticate\ndef handle(t): return authenticate(t)\n",
            encoding="utf-8",
        )
        check_inspect(tmp)
        check_pack(tmp)
    check_gitignore()
    check_cli_error()
    check_mcp()
    check_parsers()
    print("All smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
