# Roadmap

## v0.1.x stabilization

- Improve excerpt selection for large files.
- Add fixture repositories for regression testing.
- Publish benchmark methodology.
- ~~Harden CLI error messages~~ — done in 0.2.0 (issue #1).

## v0.2 language depth — shipped 2026-08-29

- ~~Add Rust and Go symbol extraction~~ — done (regex, zero-deps, #13/#14) + PHP (#17).
- ~~MCP server for Claude/Cursor/Codex~~ — done (#11) + HTTP API.
- ~~Plugin interface for analyzers~~ — done (#6, `coreball.plugins`).
- ~~`.gitignore` support~~ — done (#2).
- Richer TypeScript parsing + Java/C# still open.
- Optional tree-sitter analyzers behind extras (planned).

## v0.3 semantic graph

- Model imports, exports, symbol definitions and references as a graph.
- Add explainable graph expansion controls.
- Support package/module boundary detection.

## v0.4 benchmark suite

- Build public benchmark tasks over real open-source repositories.
- Measure package usefulness, token savings and selection stability.

## v1.0

- Stable plugin API.
- Stable context package schema.
- Language analyzers for major ecosystems.
- Production-ready performance on medium and large repositories.
