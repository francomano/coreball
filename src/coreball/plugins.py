"""Plugin interface for language analyzers.

CoreBall's v0.1 uses built-in regex/AST parsers. This module defines a
minimal, zero-dependency plugin protocol so third-party analyzers can be
registered without overengineering.

Design decisions (see docs/design-decisions.md):
- No entry-points discovery — registration is explicit via `register_analyzer`.
- Protocol is a plain callable: `(root, path) -> SourceFile | None`.
- Returning None means "not handled", next analyzer is tried.
- Built-in parsers remain the default and are always registered.
- Public API stays backward compatible: `inspect_repository` still works
  without any plugin setup.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from coreball.models import SourceFile

Analyzer = Callable[[Path, Path], SourceFile | None]


class AnalyzerPlugin(Protocol):
    """Protocol for analyzer objects (alternative to callable)."""

    def can_handle(self, language: str) -> bool:
        """Return True if this analyzer handles the given language label."""
        ...

    def parse(self, root: Path, path: Path) -> SourceFile | None:
        """Parse file or return None if not handled."""
        ...


_registry: dict[str, Analyzer] = {}
_callable_registry: list[Analyzer] = []


def register_analyzer(language: str, analyzer: Analyzer) -> None:
    """Register an analyzer for a language label.

    Args:
        language: Language label as returned by `scanner.language_for`
            (e.g. "python", "go", "rust").
        analyzer: Callable that takes (root, path) and returns a SourceFile
            or None if the file should be handled by the next analyzer.
    """
    _registry[language.lower()] = analyzer


def register_callable_analyzer(analyzer: Analyzer) -> None:
    """Register a generic analyzer tried before language-specific ones."""
    _callable_registry.append(analyzer)


def get_analyzer(language: str) -> Analyzer | None:
    """Return the registered analyzer for a language, if any."""
    return _registry.get(language.lower())


def list_analyzers() -> dict[str, Analyzer]:
    """Return a copy of the language->analyzer registry."""
    return dict(_registry)


def clear_analyzers() -> None:
    """Clear all registered analyzers (useful for testing)."""
    _registry.clear()
    _callable_registry.clear()


def parse_with_plugins(root: Path, path: Path, fallback: Analyzer) -> SourceFile:
    """Try registered analyzers before falling back to built-in parser.

    Tries generic callables first, then language-specific analyzer,
    then the provided fallback.
    """
    from coreball.scanner import language_for

    language = language_for(path)
    for analyzer in _callable_registry:
        result = analyzer(root, path)
        if result is not None:
            return result
    specific = _registry.get(language)
    if specific is not None:
        result = specific(root, path)
        if result is not None:
            return result
    fallback_result = fallback(root, path)
    # fallback should never return None, but handle defensively
    if fallback_result is None:
        raise RuntimeError(f"Fallback analyzer returned None for {path}")
    return fallback_result
