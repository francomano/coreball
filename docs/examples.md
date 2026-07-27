# Examples

## Explain a subsystem

```bash
coreball pack . --task "explain how the command line interface works" --max-tokens 1800
```

## Prepare context for a bug fix

```bash
coreball pack . --task "fix incorrect authentication error handling" --max-tokens 2400 --format markdown
```

## Machine-readable context

```bash
coreball pack . --task "identify public API models" --max-tokens 1200 --format json
```
