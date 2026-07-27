# Architecture

CoreBall v0.1 is a small Python package with a CLI and public API.

## Components

- `scanner`: deterministic repository discovery with conservative ignore rules.
- `parsers`: language-specific extraction of symbols, imports and direct calls.
- `models`: stable dataclass-based public data structures.
- `graph`: lightweight relationship inference between files.
- `selector`: task-aware scoring and token-budget packing.
- `renderers`: Markdown and JSON output formats.
- `cli`: command-line interface built on `argparse`.

## Data flow

```text
repository -> scanner -> parsers -> RepositoryModel -> selector -> ContextPackage -> renderer
```

## Design principles

- Deterministic output over opaque ranking.
- Minimal runtime dependencies.
- Explainable selection reasons.
- Public API shaped around stable models.
- Practical v0.1 functionality rather than placeholder research scaffolding.
