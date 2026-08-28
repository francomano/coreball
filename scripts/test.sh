#!/usr/bin/env bash
# CoreBall comprehensive test runner — stdlib only, no external deps required at runtime
# Runs lint, types, tests, and CLI/MCP/API smoke checks.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== CoreBall test ==="

# Prefer docker python:3.11 if host is <3.11, else use local python
PY="python"
if ! $PY -c "import sys; assert sys.version_info >= (3,11)" 2>/dev/null; then
  if command -v docker >/dev/null 2>&1; then
    echo "[test] using Docker python:3.11"
    exec docker run --rm -v "$ROOT:/workspace" -w /workspace python:3.11-slim bash -c "pip install -q -e '.[dev]' && bash scripts/test.sh"
  else
    echo "Python >=3.11 required, found: $($PY --version)"
    exit 1
  fi
fi

# Install if needed
if ! $PY -c "import pytest" 2>/dev/null; then
  echo "[test] installing dev deps..."
  $PY -m pip install -q -e ".[dev]"
fi

echo "[1/5] ruff format --check"
$PY -m ruff format --check .

echo "[2/5] ruff check"
$PY -m ruff check .

echo "[3/5] mypy src/coreball"
$PY -m mypy src/coreball

echo "[4/5] pytest"
$PY -m pytest -q

echo "[5/5] smoke tests"
$PY -m coreball.cli inspect . --format json > /tmp/cb-inspect.json
$PY -c "import json; d=json.load(open('/tmp/cb-inspect.json')); assert d['file_count']>0, 'no files'"
echo "  - inspect OK"

$PY -m coreball.cli pack . --task "explain the selector" --max-tokens 1200 --format json > /tmp/cb-pack.json
$PY -c "import json; d=json.load(open('/tmp/cb-pack.json')); assert d['estimated_tokens'] <= d['max_tokens']"
echo "  - pack OK"

# .gitignore smoke (create temp repo)
TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/sub"
echo "*.ignored" > "$TMPDIR/.gitignore"
echo "hello" > "$TMPDIR/a.py"
echo "hello" > "$TMPDIR/b.ignored"
echo "hello" > "$TMPDIR/sub/c.ignored"
$PY -c "
from pathlib import Path
from coreball.scanner import discover_files
import tempfile
root = Path('$TMPDIR')
files = discover_files(root, respect_gitignore=True)
names = {p.name for p in files}
assert 'b.ignored' not in names, names
print('  - .gitignore OK')
"
rm -rf "$TMPDIR"

# CLI error message smoke
set +e
OUT=$($PY -m coreball.cli pack . --task "x" --max-tokens 10 2>&1)
EC=$?
set -e
if [ $EC -eq 0 ]; then echo "expected failure for max_tokens=10"; exit 1; fi
if ! echo "$OUT" | grep -q "at least 128"; then echo "bad error message: $OUT"; exit 1; fi
echo "  - CLI error message OK"

# MCP smoke
printf '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n' | $PY -m coreball.mcp_server > /tmp/cb-mcp.jsonl
if ! grep -q '"tools"' /tmp/cb-mcp.jsonl; then echo "MCP failed"; cat /tmp/cb-mcp.jsonl; exit 1; fi
echo "  - MCP OK"

# Go/Rust/PHP parser smoke
$PY -c "
from pathlib import Path
import tempfile, textwrap
from coreball.parsers import _parse_go, _parse_rust, _parse_php
go = _parse_go('a.go','go',100, 'package main\nimport \"fmt\"\nfunc Hello() {}\ntype Foo struct{}\n')
assert any(s.name=='Hello' for s in go.symbols), go.symbols
assert 'fmt' in go.imports
rust = _parse_rust('a.rs','rust',100, 'use std::io;\nfn hello(){}\nstruct Foo;')
assert any(s.name=='hello' for s in rust.symbols)
php = _parse_php('a.php','php',100, '<?php\nuse Foo\\\\Bar;\nclass Baz {}\nfunction hello(){}\n')
assert any(s.name=='Baz' for s in php.symbols)
print('  - Go/Rust/PHP parsers OK')
"

echo ""
echo "All checks passed."
