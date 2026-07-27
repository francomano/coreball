"""Typed data models used by CoreBall.

The project intentionally uses dataclasses instead of a runtime validation dependency.
These models form the stable public API for v0.1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Symbol:
    """A named semantic unit discovered in a source file."""

    name: str
    kind: str
    file_path: str
    line_start: int
    line_end: int
    signature: str
    docstring: str | None = None


@dataclass(frozen=True)
class SourceFile:
    """A source file with lightweight semantic metadata."""

    path: str
    language: str
    size_bytes: int
    imports: tuple[str, ...] = ()
    symbols: tuple[Symbol, ...] = ()
    calls: tuple[str, ...] = ()
    text: str = ""


@dataclass(frozen=True)
class RepositoryModel:
    """A compact semantic index of a repository."""

    root: Path
    files: tuple[SourceFile, ...]

    @property
    def symbol_count(self) -> int:
        """Return the number of symbols in the repository model."""

        return sum(len(file.symbols) for file in self.files)


@dataclass(frozen=True)
class ContextItem:
    """One selected item in a context package."""

    path: str
    language: str
    score: float
    reason: str
    symbols: tuple[Symbol, ...] = ()
    excerpt: str = ""
    estimated_tokens: int = 0


@dataclass(frozen=True)
class ContextPackage:
    """The compact context selected for a specific task and token budget."""

    task: str
    max_tokens: int
    estimated_tokens: int
    summary: str
    items: tuple[ContextItem, ...] = field(default_factory=tuple)
    omitted_files: tuple[str, ...] = field(default_factory=tuple)
