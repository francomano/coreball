"""Repository file discovery."""

from __future__ import annotations

import fnmatch
from pathlib import Path, PurePosixPath

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
    ".php": "php",
    ".rb": "ruby",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".swift": "swift",
    ".kt": "kotlin",
}

MAX_FILE_BYTES = 250_000


def _load_gitignore_patterns(root: Path) -> list[tuple[Path, str, bool]]:
    """Load .gitignore patterns from all .gitignore files under root.

    Returns list of (base_dir, pattern, is_negation) in discovery order.
    """
    patterns: list[tuple[Path, str, bool]] = []
    for gitignore in sorted(root.rglob(".gitignore")):
        try:
            # Skip files inside DEFAULT_IGNORE_DIRS
            if any(part in DEFAULT_IGNORE_DIRS for part in gitignore.relative_to(root).parts[:-1]):
                continue
            text = gitignore.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        base = gitignore.parent.resolve()
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            is_neg = line.startswith("!")
            if is_neg:
                line = line[1:].strip()
                if not line:
                    continue
            # Ignore lines that are just "!"
            patterns.append((base, line, is_neg))
    return patterns


def _pattern_matches(pattern: str, rel_posix: str, filename: str) -> bool:
    """Check if a gitignore pattern matches a relative POSIX path."""
    # Directory pattern handling: "foo/" matches "foo" or "foo/anything"
    is_dir_pattern = pattern.endswith("/")
    core = pattern.rstrip("/") if is_dir_pattern else pattern
    # Strip leading slash (anchored to base)
    if core.startswith("/"):
        core = core[1:]
    # Empty after stripping
    if not core:
        return False
    # If pattern contains slash, match against full relative path
    if "/" in core:
        # Support ** via PurePosixPath.match fallback
        if fnmatch.fnmatch(rel_posix, core) or fnmatch.fnmatch(rel_posix, core + "/*"):
            return True
        # Use PurePosixPath.match for ** support
        try:
            if PurePosixPath(rel_posix).match(core) or PurePosixPath(rel_posix).match(core + "/*"):
                return True
        except Exception:
            pass
        # Prefix match for directory patterns
        return is_dir_pattern and (rel_posix == core or rel_posix.startswith(core + "/"))
    # No slash: match against any path component (filename or directory name)
    if fnmatch.fnmatch(filename, core):
        return True
    # Also match against any part of the path
    for part in rel_posix.split("/"):
        if fnmatch.fnmatch(part, core):
            return True
    # Also check directory prefix for patterns like "*.log" vs path
    if is_dir_pattern:
        for part in rel_posix.split("/"):
            if fnmatch.fnmatch(part, core.rstrip("/")):
                return True
    return False


def _is_ignored(path: Path, root: Path, patterns: list[tuple[Path, str, bool]]) -> bool:
    """Return True if path should be ignored per gitignore patterns."""
    if not patterns:
        return False
    ignored = False
    try:
        rel_to_root = path.relative_to(root).as_posix()
        filename = path.name
    except ValueError:
        return False
    for base, pattern, is_neg in patterns:
        try:
            rel_to_base = path.relative_to(base).as_posix()
        except ValueError:
            # Pattern base is not ancestor of path
            continue
        # Also check relative to root for root-level patterns
        # Patterns from nested .gitignore are relative to their directory
        if _pattern_matches(pattern, rel_to_base, filename) or _pattern_matches(
            pattern, rel_to_root, filename
        ):
            ignored = not is_neg
    return ignored


def discover_files(
    root: Path, *, include_docs: bool = True, respect_gitignore: bool = True
) -> list[Path]:
    """Return readable project files in deterministic order.

    Large generated files and common dependency/build directories are skipped.
    When respect_gitignore is True, .gitignore patterns are honoured without
    adding a runtime dependency.
    """

    root = root.resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repository root does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Repository root is not a directory: {root}")

    patterns = _load_gitignore_patterns(root) if respect_gitignore else []

    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in DEFAULT_IGNORE_DIRS for part in path.relative_to(root).parts):
            continue
        if respect_gitignore and _is_ignored(path, root, patterns):
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
