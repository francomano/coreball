"""Public CoreBall API."""

from __future__ import annotations

from pathlib import Path

from coreball.models import ContextPackage, RepositoryModel
from coreball.parsers import parse_file
from coreball.scanner import discover_files
from coreball.selector import select_context


def inspect_repository(
    path: str | Path, *, include_docs: bool = True, respect_gitignore: bool = True
) -> RepositoryModel:
    """Build a semantic repository model.

    Args:
        path: Repository root to inspect.
        include_docs: Whether Markdown documentation should be indexed.
        respect_gitignore: Whether to honour .gitignore patterns.

    Returns:
        A RepositoryModel containing files, symbols, imports and direct call names.
    """

    root = Path(path).resolve()
    files = tuple(
        parse_file(root, file)
        for file in discover_files(
            root, include_docs=include_docs, respect_gitignore=respect_gitignore
        )
    )
    return RepositoryModel(root=root, files=files)


def pack_repository(
    path: str | Path,
    *,
    task: str,
    max_tokens: int,
    include_docs: bool = True,
    respect_gitignore: bool = True,
) -> ContextPackage:
    """Compile a repository into a compact task-specific context package.

    Args:
        path: Repository root to inspect.
        task: User task or question the context package should support.
        max_tokens: Maximum estimated token budget.
        include_docs: Whether Markdown documentation should be considered.
        respect_gitignore: Whether to honour .gitignore patterns.

    Returns:
        A ContextPackage optimized for the task and budget.
    """

    model = inspect_repository(path, include_docs=include_docs, respect_gitignore=respect_gitignore)
    return select_context(model, task=task, max_tokens=max_tokens)
