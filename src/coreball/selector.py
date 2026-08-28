"""Task-aware context selection."""

from __future__ import annotations

import math
import re

from coreball.graph import related_files
from coreball.models import ContextItem, ContextPackage, RepositoryModel, SourceFile
from coreball.tokens import estimate_tokens

_TERM_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]*")


def select_context(model: RepositoryModel, *, task: str, max_tokens: int) -> ContextPackage:
    """Select a compact semantic context package for a task.

    The v0.1 algorithm combines lexical relevance, symbol matches and graph expansion.
    It is deterministic, explainable and intentionally small enough to be audited.
    """

    if max_tokens < 128:
        raise ValueError(
            f"Invalid --max-tokens value '{max_tokens}': must be at least 128. "
            f'Try: coreball pack <repo> --task "<your task>" --max-tokens 512'
        )

    terms = _task_terms(task)
    file_scores = {file.path: _score_file(file, terms) for file in model.files}
    graph = related_files(model)
    for path, neighbours in graph.items():
        neighbour_bonus = sum(file_scores.get(neighbour, 0.0) for neighbour in neighbours) * 0.18
        file_scores[path] += neighbour_bonus

    ranked_files = sorted(model.files, key=lambda file: (-file_scores[file.path], file.path))
    reserved = estimate_tokens(_package_header(task, max_tokens, model))
    budget = max_tokens - reserved
    items: list[ContextItem] = []
    omitted: list[str] = []
    used = reserved

    for file in ranked_files:
        score = file_scores[file.path]
        if score <= 0 and items:
            omitted.append(file.path)
            continue
        item = _context_item(file, score, terms)
        if item.estimated_tokens <= max(32, budget - (used - reserved)):
            items.append(item)
            used += item.estimated_tokens
        else:
            compact = _context_item(file, score, terms, compact=True)
            if compact.estimated_tokens <= max(32, budget - (used - reserved)):
                items.append(compact)
                used += compact.estimated_tokens
            else:
                omitted.append(file.path)

    if not items and ranked_files:
        first = _context_item(
            ranked_files[0], file_scores[ranked_files[0].path], terms, compact=True
        )
        items.append(first)
        used += first.estimated_tokens
        omitted = [file.path for file in ranked_files[1:]]

    summary = _summary(model, items, omitted)
    return ContextPackage(
        task=task,
        max_tokens=max_tokens,
        estimated_tokens=min(used + estimate_tokens(summary), max_tokens),
        summary=summary,
        items=tuple(items),
        omitted_files=tuple(omitted),
    )


def _task_terms(task: str) -> set[str]:
    return {term.lower().replace("-", "_") for term in _TERM_RE.findall(task) if len(term) > 2}


def _score_file(file: SourceFile, terms: set[str]) -> float:
    haystacks = [file.path.lower().replace("-", "_")]
    haystacks.extend(symbol.name.lower() for symbol in file.symbols)
    haystacks.extend(symbol.signature.lower() for symbol in file.symbols)
    haystacks.extend((symbol.docstring or "").lower() for symbol in file.symbols)
    haystacks.extend(imported.lower() for imported in file.imports)
    text_lower = file.text[:12_000].lower().replace("-", "_")

    score = 0.0
    for term in terms:
        if any(term in haystack for haystack in haystacks):
            score += 6.0
        score += min(4.0, text_lower.count(term) * 0.8)

    if file.symbols:
        score += math.log2(len(file.symbols) + 1)
    if file.path in {"README.md", "pyproject.toml", "package.json"}:
        score += 1.5
    return score


def _context_item(
    file: SourceFile, score: float, terms: set[str], *, compact: bool = False
) -> ContextItem:
    symbols = file.symbols
    excerpt = _excerpt(file, terms, compact=compact)
    symbol_names = ", ".join(symbol.name for symbol in symbols[:8]) or "no symbols"
    reason = (
        f"score={score:.2f}; selected for symbols/imports/text relevant to task; "
        f"symbols: {symbol_names}"
    )
    rendered = f"{file.path}\n{reason}\n{excerpt}"
    return ContextItem(
        path=file.path,
        language=file.language,
        score=round(score, 3),
        reason=reason,
        symbols=symbols[:12],
        excerpt=excerpt,
        estimated_tokens=estimate_tokens(rendered),
    )


def _excerpt(file: SourceFile, terms: set[str], *, compact: bool) -> str:
    lines = file.text.splitlines()
    if not lines:
        return ""

    selected: set[int] = set()
    for symbol in file.symbols[:12]:
        start = max(1, symbol.line_start - 1)
        end = min(len(lines), symbol.line_end + 1)
        selected.update(range(start, end + 1))

    for index, line in enumerate(lines, start=1):
        lower = line.lower().replace("-", "_")
        if any(term in lower for term in terms):
            selected.update(range(max(1, index - 2), min(len(lines), index + 2) + 1))

    if not selected:
        limit = 20 if compact else 80
        return "\n".join(lines[:limit])

    limit_lines = 35 if compact else 120
    chunks: list[str] = []
    last = 0
    for line_no in sorted(selected)[:limit_lines]:
        if last and line_no > last + 1:
            chunks.append("...")
        chunks.append(f"{line_no}: {lines[line_no - 1]}")
        last = line_no
    return "\n".join(chunks)


def _package_header(task: str, max_tokens: int, model: RepositoryModel) -> str:
    return (
        f"CoreBall context package\nTask: {task}\nBudget: {max_tokens}\nFiles: {len(model.files)}\n"
    )


def _summary(model: RepositoryModel, items: list[ContextItem], omitted: list[str]) -> str:
    selected_symbols = sum(len(item.symbols) for item in items)
    return (
        f"Selected {len(items)} of {len(model.files)} files and {selected_symbols} symbols "
        f"from a repository containing {model.symbol_count} symbols. "
        f"Omitted {len(omitted)} lower-priority files to respect the token budget."
    )
