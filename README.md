# CoreBall

<p align="center">
  <a href="https://github.com/coreball/coreball/actions"><img src="https://img.shields.io/github/actions/workflow/status/coreball/coreball/ci.yml?branch=main&label=CI&logo=github&style=flat-square" alt="CI"></a>
  <a href="https://pypi.org/project/coreball/"><img src="https://img.shields.io/pypi/v/coreball?logo=pypi&style=flat-square" alt="PyPI"></a>
  <a href="https://pypi.org/project/coreball/"><img src="https://img.shields.io/pypi/pyversions/coreball?logo=python&style=flat-square" alt="Python versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License"></a>
  <a href="https://github.com/coreball/coreball/issues"><img src="https://img.shields.io/github/issues/coreball/coreball?style=flat-square" alt="Issues"></a>
  <a href="https://github.com/coreball/coreball/stargazers"><img src="https://img.shields.io/github/stars/coreball/coreball?style=flat-square" alt="Stars"></a>
</p>

**CoreBall** captures the core semantic context of a codebase for a specific LLM task — no RAG, no embeddings, no bloat.

Current LLM coding workflows often send entire files, arbitrary chunks, or embedding matches that are only loosely related to the user's question. That wastes tokens and can hide the important relationships the model needs: symbols, imports, call sites, entry points, and the parts of files that explain why they matter.

CoreBall's goal is different from "better RAG". It is a semantic compiler for software repositories: given a repository, a task, and a token budget, it emits the smallest structured context package that still preserves the information an LLM needs to reason about the task.

Version 0.1 is intentionally limited, but real. It scans Python, JavaScript, TypeScript, Markdown and common project metadata files; extracts symbols/imports/calls where supported; ranks files against a task; expands relevance through lightweight relationships; and renders a compact package as Markdown or JSON.

## Installation

```bash
python -m pip install -e ".[dev]"
```

## CLI usage

Inspect a repository:

```bash
coreball inspect . --format markdown
```

Create a task-specific context package:

```bash
coreball pack . --task "explain how authentication requests are handled" --max-tokens 2048
```

Write JSON output:

```bash
coreball pack . --task "find the CLI entry point" --max-tokens 1200 --format json --output coreball-context.json
```

## Python API

```python
from coreball import inspect_repository, pack_repository

model = inspect_repository(".")
package = pack_repository(
    ".",
    task="explain how the CLI builds a context package",
    max_tokens=2048,
)
```

## How v0.1 works

1. Discover source and documentation files while skipping dependency/build directories.
2. Parse Python with `ast` and JavaScript/TypeScript with conservative regex-based extraction.
3. Build a lightweight semantic model containing files, symbols, imports and direct call names.
4. Score files against the task using lexical matches, symbol matches and documentation text.
5. Expand relevance through inferred import/call relationships.
6. Pack excerpts and symbol metadata until the estimated token budget is reached.
7. Render a structured Markdown or JSON context package.

## Features

- **Zero runtime dependencies** — pure Python standard library, nothing to install
- **Deterministic** — same input, same output, every time. No embedding drift.
- **Language-aware** — understands Python (AST) and JS/TS (regex), with symbol and import resolution
- **Task-scoped** — scores and selects only what matters for your specific question
- **Token-budget control** — fits exactly within your LLM's context window
- **Dual output** — Markdown for human reading, JSON for programmatic use
- **Explainable** — every file inclusion can be traced back to a task match or relationship

## Why existing approaches are insufficient

- Whole-file prompting is simple but quickly exceeds context windows.
- Chunk retrieval often loses symbol boundaries and cross-file relationships.
- Embeddings can find topical similarity but do not understand call graphs or API surfaces.
- Dependency graphs alone identify structure but not task relevance.

CoreBall combines semantic structure and task relevance in a deterministic package that can be inspected, tested and improved.

## Limitations

- Token counts are estimates, not tokenizer-specific counts.
- Python support is stronger than JavaScript/TypeScript support.
- Relationship inference is intentionally shallow in v0.1.
- It does not yet execute build systems or use language servers.
- It does not claim to solve repository understanding as a research problem.

## Development

```bash
python -m pip install -e ".[dev]"
ruff format --check .
ruff check .
mypy src/coreball
pytest
python -m build
```

## Contributing

Contributions of all sizes are welcome! Here are some ways to help:

- **Add a language parser** — Rust, Go, Java, or any other language
- **Improve the relationship graph** — cross-file refs, call-chain expansion
- **Write tests** — increase coverage and edge cases
- **Documentation** — examples, guides, better explanations
- **Bug reports & feature requests** — open an [issue](https://github.com/coreball/coreball/issues)

See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

## License

CoreBall is released under the MIT License.
