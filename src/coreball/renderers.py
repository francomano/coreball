"""Render CoreBall models and context packages."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from coreball.models import ContextPackage, RepositoryModel


def render_inspection(model: RepositoryModel, *, fmt: str) -> str:
    """Render a repository model as json or markdown."""

    if fmt == "json":
        data: dict[str, Any] = {
            "root": str(model.root),
            "file_count": len(model.files),
            "symbol_count": model.symbol_count,
            "files": [asdict(file) | {"text": ""} for file in model.files],
        }
        return json.dumps(data, indent=2, sort_keys=True)
    if fmt == "markdown":
        lines = ["# CoreBall Repository Inspection", ""]
        lines.append(f"- Files: {len(model.files)}")
        lines.append(f"- Symbols: {model.symbol_count}")
        lines.append("")
        for file in model.files:
            lines.append(f"## `{file.path}`")
            lines.append(f"- Language: {file.language}")
            lines.append(f"- Imports: {', '.join(file.imports) if file.imports else 'none'}")
            if file.symbols:
                lines.append("- Symbols:")
                for symbol in file.symbols:
                    lines.append(
                        f"  - `{symbol.signature}` lines {symbol.line_start}-{symbol.line_end}"
                    )
            else:
                lines.append("- Symbols: none")
            lines.append("")
        return "\n".join(lines)
    raise ValueError(f"Unsupported format: {fmt}")


def render_package(package: ContextPackage, *, fmt: str) -> str:
    """Render a context package as json or markdown."""

    if fmt == "json":
        return json.dumps(asdict(package), indent=2, sort_keys=True)
    if fmt == "markdown":
        lines = ["# CoreBall Context Package", ""]
        lines.append(f"**Task:** {package.task}")
        lines.append(f"**Budget:** {package.max_tokens} estimated tokens")
        lines.append(f"**Estimated tokens:** {package.estimated_tokens}")
        lines.append("")
        lines.append("## Summary")
        lines.append(package.summary)
        lines.append("")
        for item in package.items:
            lines.append(f"## `{item.path}`")
            lines.append(f"- Language: {item.language}")
            lines.append(f"- Score: {item.score}")
            lines.append(f"- Reason: {item.reason}")
            if item.symbols:
                lines.append("- Symbols:")
                for symbol in item.symbols:
                    location = f"lines {symbol.line_start}-{symbol.line_end}"
                    lines.append(f"  - `{symbol.signature}` ({symbol.kind}, {location})")
            lines.append("")
            lines.append("```text")
            lines.append(item.excerpt)
            lines.append("```")
            lines.append("")
        if package.omitted_files:
            lines.append("## Omitted files")
            for path in package.omitted_files:
                lines.append(f"- `{path}`")
            lines.append("")
        return "\n".join(lines)
    raise ValueError(f"Unsupported format: {fmt}")
