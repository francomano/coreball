#!/usr/bin/env python3
"""Simple CoreBall benchmark runner."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from coreball import pack_repository


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark CoreBall packing runtime.")
    parser.add_argument("repository", type=Path)
    parser.add_argument("--task", required=True)
    parser.add_argument("--max-tokens", type=int, default=2048)
    args = parser.parse_args()

    start = time.perf_counter()
    package = pack_repository(args.repository, task=args.task, max_tokens=args.max_tokens)
    elapsed = time.perf_counter() - start

    print(f"repository={args.repository.resolve()}")
    print(f"selected_files={len(package.items)}")
    print(f"estimated_tokens={package.estimated_tokens}")
    print(f"elapsed_seconds={elapsed:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
