"""Token estimation utilities.

CoreBall v0.1 deliberately avoids tokenizer-specific dependencies. The estimator is
simple, deterministic and conservative enough for packing decisions.
"""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+|[^\s]")


def estimate_tokens(text: str) -> int:
    """Estimate the number of LLM tokens needed for text.

    The implementation counts lexical fragments and punctuation, then applies a
    small multiplier to avoid under-budgeting on dense source code.
    """

    if not text:
        return 0
    lexical_units = len(_TOKEN_RE.findall(text))
    return max(1, int(lexical_units * 1.15))
