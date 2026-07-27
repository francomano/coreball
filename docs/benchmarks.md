# Benchmarks

CoreBall v0.1 includes a small benchmark script to measure runtime and package size against this repository or another local repository.

```bash
python scripts/benchmark.py . --task "explain the context selector" --max-tokens 2048
```

The current benchmark is intentionally simple. Future benchmarks should measure:

- Runtime by repository size.
- Token reduction compared with whole-file prompting.
- Stability of selected context under small task wording changes.
- Human usefulness for real maintenance tasks.
