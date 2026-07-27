from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from coreball import inspect_repository, pack_repository
from coreball.renderers import render_package


def make_repo(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("Demo service with authentication.\n", encoding="utf-8")
    pkg = tmp_path / "demo"
    pkg.mkdir()
    (pkg / "auth.py").write_text(
        '''"""Authentication helpers."""

class User:
    """Application user."""

    def __init__(self, name):
        self.name = name


def authenticate(token):
    """Validate an access token."""
    return token == "secret"
''',
        encoding="utf-8",
    )
    (pkg / "api.py").write_text(
        """from demo.auth import authenticate


def handle_request(token):
    if authenticate(token):
        return "ok"
    return "denied"
""",
        encoding="utf-8",
    )
    (pkg / "ui.js").write_text(
        "export function renderLogin() { return authenticateInput(); }\n",
        encoding="utf-8",
    )
    return tmp_path


def test_inspect_repository_extracts_python_symbols(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    model = inspect_repository(repo)
    symbols = {symbol.name for file in model.files for symbol in file.symbols}
    assert "authenticate" in symbols
    assert "User" in symbols
    assert model.symbol_count >= 4


def test_pack_repository_selects_relevant_context(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    package = pack_repository(repo, task="fix authentication request handling", max_tokens=900)
    selected_paths = {item.path for item in package.items}
    assert "demo/auth.py" in selected_paths
    assert package.estimated_tokens <= package.max_tokens
    assert "Selected" in package.summary


def test_markdown_renderer_contains_excerpts(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    package = pack_repository(repo, task="explain authenticate", max_tokens=900)
    rendered = render_package(package, fmt="markdown")
    assert "# CoreBall Context Package" in rendered
    assert "authenticate" in rendered


def test_cli_inspect_json(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "coreball.cli", "inspect", str(repo), "--format", "json"],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    assert payload["symbol_count"] >= 4


def test_cli_pack_markdown(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "coreball.cli",
            "pack",
            str(repo),
            "--task",
            "debug authentication",
            "--max-tokens",
            "800",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    assert "CoreBall Context Package" in result.stdout
    assert "auth.py" in result.stdout
