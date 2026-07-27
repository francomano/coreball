# Initial issue backlog

These issues are ready to copy into GitHub after repository publication.

## Good first issues

### Improve CLI error messages for invalid token budgets

When `--max-tokens` is too small, the CLI returns an error from the selector. Add a clearer message that explains the minimum and suggests a valid command.

Acceptance criteria:
- Add a regression test.
- Error message mentions the invalid value and minimum value.
- Documentation remains accurate.

### Add `.gitignore` pattern support

CoreBall currently uses built-in ignore directories. Add optional support for reading simple `.gitignore` patterns.

Acceptance criteria:
- Supports common file and directory ignore patterns.
- Includes tests with nested ignored files.
- Does not add a runtime dependency.

## Language support

### Add Rust symbol extraction

Implement extraction for Rust functions, structs, enums, traits and modules.

Acceptance criteria:
- Parser tests cover public/private items.
- `inspect` output includes Rust symbols.
- `pack` can rank Rust files by task terms.

### Add Go symbol extraction

Implement extraction for Go functions, methods, structs and interfaces.

Acceptance criteria:
- Parser tests cover package-level functions and receiver methods.
- Imports are captured.
- Documentation includes current limitations.

## Architecture

### Introduce a versioned context package schema

Define a JSON schema for the context package so integrations can depend on a stable contract.

Acceptance criteria:
- Add schema under `schema/`.
- Validate renderer output in tests.
- Document schema versioning policy.

### Add plugin interface for analyzers

Design a minimal interface for language analyzers without overengineering.

Acceptance criteria:
- Existing parsers conform to the interface.
- Public API remains backward compatible.
- Design decision is documented.

## Research and algorithms

### Evaluate ranking quality on fixture tasks

Create a small benchmark with known relevant files and measure whether CoreBall selects them under budget.

Acceptance criteria:
- Add fixture repositories.
- Add scoring report script.
- Document baseline results.

### Improve call graph precision for Python

Use AST scopes to distinguish local functions, methods and imported symbols.

Acceptance criteria:
- Add tests for same-name functions in different modules.
- Selection quality improves for cross-file calls.
- No runtime dependency added.

## Performance

### Add incremental repository indexing

Cache parsed file metadata keyed by path, size and modification time.

Acceptance criteria:
- Cache can be disabled.
- Tests cover invalidation.
- Benchmark shows speedup on repeated runs.

## Documentation

### Add real-world walkthrough

Write a tutorial that runs CoreBall on a small public repository and explains each selected file.

Acceptance criteria:
- Tutorial command outputs match current CLI behavior.
- Includes Markdown and JSON examples.
- Mentions limitations honestly.
