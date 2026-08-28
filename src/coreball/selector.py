"""Intelligent file selector – picks the most relevant files for a task.

Uses TF-IDF scoring with path boosting, phrase matching, and
multilingual stopword filtering to rank files by relevance to a
natural-language query.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Sequence

from .models import ContextItem, ContextPackage, RepositoryModel, SourceFile, Symbol
from .tokens import estimate_tokens

__all__ = ["select_context"]

# ---------------------------------------------------------------------------
# Stopwords (English + Italian + code noise)
# ---------------------------------------------------------------------------

_STOPWORDS: set[str] = {
    # English
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "of", "in", "to",
    "for", "with", "on", "at", "from", "by", "about", "as", "into",
    "through", "during", "before", "after", "above", "below", "between",
    "out", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too",
    "very", "just", "because", "but", "and", "or", "if", "while",
    "that", "this", "these", "those", "it", "its", "i", "me", "my",
    "we", "our", "you", "your", "he", "him", "his", "she", "her",
    "they", "them", "their", "what", "which", "who", "whom",
    "up", "down", "also", "get", "got",
    # Italian
    "il", "lo", "la", "le", "li", "gli", "un", "uno", "una",
    "di", "del", "dello", "della", "dei", "degli", "delle",
    "da", "dal", "dallo", "dalla", "dai", "dagli", "dalle",
    "su", "sul", "sullo", "sulla", "sui", "sugli", "sulle",
    "con", "per", "tra", "fra", "che", "chi", "cui", "non",
    "sono", "sia", "sei", "siamo", "siete", "era", "erano",
    "ha", "ho", "hai", "hanno", "abbiamo", "avete",
    "nel", "nello", "nella", "nei", "negli", "nelle",
    "al", "allo", "alla", "ai", "agli", "alle",
    "ma", "se", "come", "dove", "quando", "anche",
    "ci", "ne", "mi", "ti", "si", "vi", "ce", "ve",
    "questo", "questa", "questi", "queste", "quello", "quella",
    "quelli", "quelle", "suo", "sua", "suoi", "sue",
    "nostro", "nostra", "nostri", "nostre",
    "loro", "tutto", "tutti", "tutta", "tutte",
    "altro", "altra", "altri", "altre", "stesso", "stessa",
    "ogni", "qualche", "alcuno", "nessuno", "molto", "poco",
    # Code noise – too generic to be useful
    "def", "class", "return", "import", "self", "none",
    "true", "false", "null", "var", "let", "const", "new",
}

# ---------------------------------------------------------------------------
# Tokenisation helpers
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[\w]+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    """Lowercase tokenize, splitting camelCase and snake_case."""
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = text.replace("_", " ")
    return [t.lower() for t in _TOKEN_RE.findall(text) if len(t) >= 2]


def _extract_query_terms(task: str) -> list[str]:
    """Extract meaningful query terms (no stopwords, len >= 2)."""
    tokens = _tokenize(task)
    return [t for t in tokens if t not in _STOPWORDS]


def _extract_query_phrases(task: str) -> list[tuple[str, ...]]:
    """Extract consecutive non-stopword bigrams/trigrams from the query."""
    tokens = _tokenize(task)
    meaningful = [(i, t) for i, t in enumerate(tokens) if t not in _STOPWORDS]
    phrases: list[tuple[str, ...]] = []
    for k in range(len(meaningful) - 1):
        idx_a, tok_a = meaningful[k]
        idx_b, tok_b = meaningful[k + 1]
        if idx_b - idx_a <= 2:
            phrases.append((tok_a, tok_b))
    for k in range(len(meaningful) - 2):
        idx_a, tok_a = meaningful[k]
        idx_c, tok_c = meaningful[k + 2]
        if idx_c - idx_a <= 4:
            _, tok_b = meaningful[k + 1]
            phrases.append((tok_a, tok_b, tok_c))
    return phrases


# ---------------------------------------------------------------------------
# IDF computation
# ---------------------------------------------------------------------------

def _compute_idf(
    terms: list[str], files: Sequence[SourceFile],
) -> dict[str, float]:
    """Compute inverse document frequency for each query term."""
    n = len(files)
    if n == 0:
        return {t: 1.0 for t in terms}

    doc_freq: dict[str, int] = {t: 0 for t in terms}
    for sf in files:
        blob = _file_text(sf).lower()
        for t in terms:
            if t in blob:
                doc_freq[t] += 1

    idf: dict[str, float] = {}
    for t in terms:
        df = doc_freq[t]
        idf[t] = math.log((n + 1) / (df + 1)) + 1.0
    return idf


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _file_text(sf: SourceFile) -> str:
    """Build a searchable text blob from a SourceFile."""
    parts: list[str] = [sf.path]
    if sf.text:
        parts.append(sf.text)
    for sym in sf.symbols:
        parts.append(sym.name)
        if sym.signature:
            parts.append(sym.signature)
        if sym.docstring:
            parts.append(sym.docstring)
    return "\n".join(parts)


def _path_text(sf: SourceFile) -> str:
    """Return the file path with separators expanded for matching."""
    return (
        sf.path
        .replace("/", " ").replace("\\", " ")
        .replace("_", " ").replace("-", " ").replace(".", " ")
        .lower()
    )


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

@dataclass
class _Score:
    sf: SourceFile
    tf_idf: float = 0.0
    path_boost: float = 0.0
    phrase: float = 0.0
    symbol: float = 0.0
    dependency: float = 0.0
    matched_terms: set[str] = field(default_factory=set)

    @property
    def total(self) -> float:
        return self.tf_idf + self.path_boost + self.phrase + self.symbol + self.dependency


def _score_file(
    sf: SourceFile,
    terms: list[str],
    idf: dict[str, float],
    phrases: list[tuple[str, ...]],
) -> _Score:
    """Score a single file against the query."""
    sc = _Score(sf=sf)
    if not terms:
        return sc

    full_text = _file_text(sf).lower()
    full_tokens = _tokenize(full_text)
    path_lower = _path_text(sf)

    # --- TF-IDF scoring ---
    token_count = len(full_tokens) or 1
    for term in terms:
        tf_raw = full_tokens.count(term)
        if tf_raw == 0:
            tf_raw = full_text.count(term)
        if tf_raw > 0:
            sc.matched_terms.add(term)
            tf = 1.0 + math.log(1 + tf_raw)
            tf_norm = tf / (1.0 + math.log(1 + token_count))
            sc.tf_idf += tf_norm * idf.get(term, 1.0)

    # --- Coverage bonus ---
    if len(terms) > 1:
        coverage = len(sc.matched_terms) / len(terms)
        sc.tf_idf *= (0.5 + 0.5 * coverage * coverage) * 2.0

    # --- Path / filename boost ---
    path_matches = 0
    for term in terms:
        if term in path_lower:
            path_matches += 1
            sc.path_boost += idf.get(term, 1.0) * 3.0
    if path_matches >= 2:
        sc.path_boost *= 1.5

    # --- Phrase matching ---
    searchable = full_text.replace("_", " ").replace("-", " ")
    for phrase in phrases:
        phrase_str = " ".join(phrase)
        if phrase_str in searchable:
            sc.phrase += len(phrase) * 4.0 * max(idf.get(p, 1.0) for p in phrase)
        if phrase_str in path_lower:
            sc.phrase += len(phrase) * 6.0 * max(idf.get(p, 1.0) for p in phrase)

    # --- Symbol relevance ---
    sym_names = [s.name.lower() for s in sf.symbols]
    sym_text = " ".join(sym_names)
    for term in terms:
        if term in sym_text:
            sc.symbol += idf.get(term, 1.0) * 2.0
    for sn in sym_names:
        if "handler" in sn or "lambda_handler" in sn:
            for term in terms:
                if "lambda" in term or "handler" in term:
                    sc.symbol += 3.0
                    break

    # --- Dependency / import relevance ---
    if sf.imports:
        imports_lower = " ".join(sf.imports).lower()
        for term in terms:
            if term in imports_lower:
                sc.dependency += idf.get(term, 1.0) * 0.5

    return sc


# ---------------------------------------------------------------------------
# Excerpt builder
# ---------------------------------------------------------------------------

def _build_excerpt(sf: SourceFile, max_lines: int = 40) -> str:
    """Return the first *max_lines* of the file text as an excerpt."""
    if not sf.text:
        return ""
    lines = sf.text.split("\n")
    return "\n".join(lines[:max_lines])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def select_context(
    model: RepositoryModel,
    *,
    task: str,
    max_tokens: int = 4096,
) -> ContextPackage:
    """Select the most relevant files for *task* within a token budget.

    Ranking uses TF-IDF with path boosting, phrase matching, and
    coverage bonuses.  Stopwords are filtered to avoid noise.
    """
    files = model.files

    if not files:
        return ContextPackage(
            task=task,
            max_tokens=max_tokens,
            estimated_tokens=0,
            summary="No files to select from.",
            items=(),
            omitted_files=(),
        )

    # --- Extract query terms and phrases ---
    terms = _extract_query_terms(task)
    phrases = _extract_query_phrases(task)

    # If ALL terms got filtered as stopwords, fall back to raw tokens
    if not terms:
        terms = _tokenize(task)

    # --- Compute IDF across the corpus ---
    idf = _compute_idf(terms, files)

    # --- Score every file ---
    scored: list[_Score] = [_score_file(sf, terms, idf, phrases) for sf in files]

    # --- Sort by total score descending ---
    scored.sort(key=lambda s: s.total, reverse=True)

    # --- Greedy knapsack: pack files within budget ---
    items: list[ContextItem] = []
    omitted: list[str] = []
    total_tok = 0

    for sc in scored:
        sf = sc.sf
        if sc.total <= 0:
            omitted.append(sf.path)
            continue

        excerpt = _build_excerpt(sf)
        ftok = estimate_tokens(excerpt) if excerpt else estimate_tokens(sf.text or "")

        if total_tok + ftok > max_tokens and items:
            omitted.append(sf.path)
            continue

        # Build reason string
        parts = [f"score={sc.total:.2f}"]
        if sc.path_boost > 0:
            parts.append(f"path_boost={sc.path_boost:.1f}")
        if sc.phrase > 0:
            parts.append(f"phrase={sc.phrase:.1f}")
        if sc.matched_terms:
            parts.append(f"terms={','.join(sorted(sc.matched_terms))}")
        sym_names = [s.name for s in sf.symbols[:5]]
        if sym_names:
            parts.append(f"symbols: {', '.join(sym_names)}")
        reason = "; ".join(parts)

        item = ContextItem(
            path=sf.path,
            language=sf.language or "",
            score=round(sc.total, 3),
            reason=reason,
            symbols=tuple(sf.symbols),
            excerpt=excerpt,
            estimated_tokens=ftok,
        )
        items.append(item)
        total_tok += ftok

        if total_tok >= max_tokens:
            break

    # Remaining scored > 0 that didn't fit
    for sc in scored:
        if sc.total > 0 and sc.sf.path not in {it.path for it in items} and sc.sf.path not in omitted:
            omitted.append(sc.sf.path)

    all_symbols = sum(len(sf.symbols) for sf in files)
    sel_symbols = sum(len(it.symbols) for it in items)
    summary = (
        f"Selected {len(items)} of {len(files)} files and "
        f"{sel_symbols} symbols from a repository containing "
        f"{all_symbols} symbols. "
        f"Omitted {len(omitted)} lower-priority files to respect the token budget."
    )

    return ContextPackage(
        task=task,
        max_tokens=max_tokens,
        estimated_tokens=total_tok,
        summary=summary,
        items=tuple(items),
        omitted_files=tuple(omitted),
    )
