"""Language parsers for CoreBall's v0.1 semantic index."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from coreball.models import SourceFile, Symbol
from coreball.scanner import language_for

_JS_IMPORT_RE = re.compile(r"^\s*import\s+(?:.+?\s+from\s+)?['\"]([^'\"]+)['\"]", re.MULTILINE)
_JS_REQUIRE_RE = re.compile(r"require\(['\"]([^'\"]+)['\"]\)")
_JS_SYMBOL_RE = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?function\s+(?P<fn>[A-Za-z_$][\w$]*)\s*\([^)]*\)"
    r"|^\s*(?:export\s+)?class\s+(?P<class>[A-Za-z_$][\w$]*)"
    r"|^\s*(?:export\s+)?(?:const|let|var)\s+(?P<const>[A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
    re.MULTILINE,
)
_JS_CALL_RE = re.compile(r"\b([A-Za-z_$][\w$]*)\s*\(")


def parse_file(root: Path, path: Path) -> SourceFile:
    """Parse a source file into a SourceFile model."""

    rel_path = str(path.relative_to(root))
    text = path.read_text(encoding="utf-8", errors="replace")
    language = language_for(path)
    size_bytes = path.stat().st_size

    if language == "python":
        return _parse_python(rel_path, language, size_bytes, text)
    if language in {"javascript", "typescript"}:
        return _parse_javascript_like(rel_path, language, size_bytes, text)
    return SourceFile(path=rel_path, language=language, size_bytes=size_bytes, text=text)


def _parse_python(path: str, language: str, size_bytes: int, text: str) -> SourceFile:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return SourceFile(path=path, language=language, size_bytes=size_bytes, text=text)

    imports: list[str] = []
    symbols: list[Symbol] = []
    calls: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append("." * node.level + module)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(_python_symbol(path, node))
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name:
                calls.add(name)

    return SourceFile(
        path=path,
        language=language,
        size_bytes=size_bytes,
        imports=tuple(sorted(set(imports))),
        symbols=tuple(sorted(symbols, key=lambda s: (s.line_start, s.name))),
        calls=tuple(sorted(calls)),
        text=text,
    )


def _python_symbol(
    path: str, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
) -> Symbol:
    if isinstance(node, ast.ClassDef):
        kind = "class"
        signature = f"class {node.name}"
    else:
        kind = "function"
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        args = ", ".join(arg.arg for arg in node.args.args)
        signature = f"{prefix} {node.name}({args})"

    return Symbol(
        name=node.name,
        kind=kind,
        file_path=path,
        line_start=getattr(node, "lineno", 1),
        line_end=getattr(node, "end_lineno", getattr(node, "lineno", 1)),
        signature=signature,
        docstring=ast.get_docstring(node),
    )


def _call_name(func: ast.expr) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _parse_javascript_like(path: str, language: str, size_bytes: int, text: str) -> SourceFile:
    imports = set(_JS_IMPORT_RE.findall(text)) | set(_JS_REQUIRE_RE.findall(text))
    symbols: list[Symbol] = []
    for match in _JS_SYMBOL_RE.finditer(text):
        name = match.group("fn") or match.group("class") or match.group("const")
        if not name:
            continue
        line_start = text.count("\n", 0, match.start()) + 1
        kind = "class" if match.group("class") else "function"
        signature = text[match.start() : text.find("\n", match.start())].strip()
        symbols.append(
            Symbol(
                name=name,
                kind=kind,
                file_path=path,
                line_start=line_start,
                line_end=line_start,
                signature=signature,
            )
        )

    calls = {
        name for name in _JS_CALL_RE.findall(text) if name not in {"if", "for", "while", "switch"}
    }
    return SourceFile(
        path=path,
        language=language,
        size_bytes=size_bytes,
        imports=tuple(sorted(imports)),
        symbols=tuple(sorted(symbols, key=lambda s: (s.line_start, s.name))),
        calls=tuple(sorted(calls)),
        text=text,
    )
