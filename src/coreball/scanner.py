"""Repository file discovery."""

from __future__ import annotations

from pathlib import Path

DEFAULT_IGNORE_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "node_modules",
        "dist",
        "build",
        ".venv",
        "venv",
        "target",
        ".idea",
        ".vscode",
    }
)

LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".md": "markdown",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".rs": "rust",
    ".go": "go",
    ".java": "java",
}

MAX_FILE_BYTES = 250_000


def discover_files(root: Path, *, include_docs: bool = True) -> list[Path]:
    """Return readable project files in deterministic order.

    Large generated files and common dependency/build directories are skipped.
    """

    root = root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repository root is not a directory: {root}")

    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in DEFAULT_IGNORE_DIRS for part in path.relative_to(root).parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in LANGUAGE_BY_SUFFIX:
            continue
        if not include_docs and LANGUAGE_BY_SUFFIX[path.suffix.lower()] == "markdown":
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        files.append(path)
    return sorted(files, key=lambda p: str(p.relative_to(root)))


def language_for(path: Path) -> str:
    """Return CoreBall's language label for a path."""

    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "text")
