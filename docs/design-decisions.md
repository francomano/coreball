# Design decisions

## Python first

Python provides a mature standard-library AST and is common in LLM tooling. CoreBall starts there while leaving room for language-server-backed analyzers later.

## No runtime dependencies

The v0.1 CLI and library depend only on the Python standard library. This keeps installation simple and avoids dependency churn for early adopters.

## Dataclasses instead of validation frameworks

CoreBall's internal models are small and stable. Dataclasses make the public API readable without introducing a schema dependency.

## Conservative token estimation

Tokenizer-specific counting would require model-specific dependencies. v0.1 uses a deterministic lexical estimate with a conservative multiplier.

## Regex JavaScript/TypeScript parsing

The JavaScript/TypeScript parser is deliberately conservative. It extracts common imports, functions, classes and arrow-function exports without pretending to be a full compiler.

## Markdown and JSON output

Markdown is immediately useful for LLM prompts. JSON is useful for automation and future integrations.
