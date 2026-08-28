"""Language parsers for CoreBall's v0.1 semantic index."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from coreball.models import SourceFile, Symbol
from coreball.scanner import language_for

# Plugin support is optional to avoid circular import at module load time
# parsers.parse_file will try plugins registry before built-in logic.

_JS_IMPORT_RE = re.compile(r"^\s*import\s+(?:.+?\s+from\s+)?['\"]([^'\"]+)['\"]", re.MULTILINE)
_JS_REQUIRE_RE = re.compile(r"require\(['\"]([^'\"]+)['\"]\)")
_JS_SYMBOL_RE = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?function\s+(?P<fn>[A-Za-z_$][\w$]*)\s*\([^)]*\)"
    r"|^\s*(?:export\s+)?class\s+(?P<class>[A-Za-z_$][\w$]*)"
    r"|^\s*(?:export\s+)?(?:const|let|var)\s+(?P<const>[A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
    re.MULTILINE,
)
_JS_CALL_RE = re.compile(r"\b([A-Za-z_$][\w$]*)\s*\(")

# Go patterns
_GO_IMPORT_BLOCK_RE = re.compile(r"import\s*\(\s*(?P<body>.*?)\s*\)", re.DOTALL)
_GO_IMPORT_SINGLE_RE = re.compile(r'^\s*import\s+(?:\w+\s+)?"([^"]+)"', re.MULTILINE)
_GO_FUNC_RE = re.compile(r"^\s*func\s+(?:\([^)]+\)\s+)?(?P<name>[A-Za-z_]\w*)\s*\(", re.MULTILINE)
_GO_TYPE_RE = re.compile(
    r"^\s*type\s+(?P<name>[A-Za-z_]\w*)\s+(?:struct|interface|[\w\[\]\*]+)", re.MULTILINE
)
_GO_CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")

# Rust patterns
_RUST_USE_RE = re.compile(r"^\s*use\s+([^;]+);", re.MULTILINE)
_RUST_FN_RE = re.compile(
    r"^\s*(?:pub(?:\([^)]+\))?\s+)?(?:async\s+)?fn\s+(?P<name>[A-Za-z_]\w*)", re.MULTILINE
)
_RUST_STRUCT_RE = re.compile(
    r"^\s*(?:pub(?:\([^)]+\))?\s+)?struct\s+(?P<name>[A-Za-z_]\w*)", re.MULTILINE
)
_RUST_ENUM_RE = re.compile(
    r"^\s*(?:pub(?:\([^)]+\))?\s+)?enum\s+(?P<name>[A-Za-z_]\w*)", re.MULTILINE
)
_RUST_TRAIT_RE = re.compile(
    r"^\s*(?:pub(?:\([^)]+\))?\s+)?trait\s+(?P<name>[A-Za-z_]\w*)", re.MULTILINE
)
_RUST_MOD_RE = re.compile(
    r"^\s*(?:pub(?:\([^)]+\))?\s+)?mod\s+(?P<name>[A-Za-z_]\w*)", re.MULTILINE
)
_RUST_IMPL_RE = re.compile(r"^\s*impl(?:<[^>]+>)?\s+(?:\w+::)?(?P<name>[A-Za-z_]\w*)", re.MULTILINE)
_RUST_CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*(?:\(|::)")

# PHP patterns
_PHP_USE_RE = re.compile(r"^\s*use\s+([^;]+);", re.MULTILINE)
_PHP_NAMESPACE_RE = re.compile(r"^\s*namespace\s+([^;]+);", re.MULTILINE)
_PHP_CLASS_RE = re.compile(
    r"^\s*(?:abstract\s+|final\s+)?class\s+(?P<name>[A-Za-z_]\w*)", re.MULTILINE
)
_PHP_INTERFACE_RE = re.compile(r"^\s*interface\s+(?P<name>[A-Za-z_]\w*)", re.MULTILINE)
_PHP_TRAIT_RE = re.compile(r"^\s*trait\s+(?P<name>[A-Za-z_]\w*)", re.MULTILINE)
_PHP_FUNC_RE = re.compile(
    r"^\s*(?:public|private|protected|static|\s)*function\s+(?P<name>[A-Za-z_]\w*)\s*\(",
    re.MULTILINE,
)
_PHP_CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")


def parse_file(root: Path, path: Path) -> SourceFile:
    """Parse a source file into a SourceFile model.

    Checks for a registered plugin analyzer first; if none handles the file,
    falls back to the built-in language parsers. This keeps the public API
    backward compatible while enabling the plugin interface from issue #6.
    """

    # Try plugin analyzers before built-in ones
    try:
        from coreball.plugins import _callable_registry as _callables
        from coreball.plugins import get_analyzer as _get_analyzer
        from coreball.scanner import language_for as _lang_for

        lang = _lang_for(path)
        for _analyzer in list(_callables):
            _result = _analyzer(root, path)
            if _result is not None:
                return _result
        _specific = _get_analyzer(lang)
        if _specific is not None:
            _result = _specific(root, path)
            if _result is not None:
                return _result
    except Exception:
        # Plugin failures must not break core parsing; fall back to built-ins
        pass

    rel_path = str(path.relative_to(root))
    text = path.read_text(encoding="utf-8", errors="replace")
    language = language_for(path)
    size_bytes = path.stat().st_size

    if language == "python":
        return _parse_python(rel_path, language, size_bytes, text)
    if language in {"javascript", "typescript"}:
        return _parse_javascript_like(rel_path, language, size_bytes, text)
    if language == "go":
        return _parse_go(rel_path, language, size_bytes, text)
    if language == "rust":
        return _parse_rust(rel_path, language, size_bytes, text)
    if language == "php":
        return _parse_php(rel_path, language, size_bytes, text)
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


def _parse_go(path: str, language: str, size_bytes: int, text: str) -> SourceFile:
    imports: set[str] = set()
    for m in _GO_IMPORT_SINGLE_RE.finditer(text):
        imports.add(m.group(1))
    for block in _GO_IMPORT_BLOCK_RE.finditer(text):
        body = block.group("body")
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            # Extract quoted import
            q = re.search(r'"([^"]+)"', line)
            if q:
                imports.add(q.group(1))
    symbols: list[Symbol] = []
    for match in _GO_FUNC_RE.finditer(text):
        name = match.group("name")
        line_start = text.count("\n", 0, match.start()) + 1
        sig = text[match.start() : text.find("\n", match.start())].strip()
        if len(sig) > 150:
            sig = sig[:150]
        symbols.append(
            Symbol(
                name=name,
                kind="function",
                file_path=path,
                line_start=line_start,
                line_end=line_start,
                signature=sig,
            )
        )
    for match in _GO_TYPE_RE.finditer(text):
        name = match.group("name")
        line_start = text.count("\n", 0, match.start()) + 1
        sig = text[match.start() : text.find("\n", match.start())].strip()
        kind = "class" if "struct" in sig or "interface" in sig else "type"
        # avoid duplicate if already captured as func receiver type? keep simple
        if any(s.name == name and s.line_start == line_start for s in symbols):
            continue
        symbols.append(
            Symbol(
                name=name,
                kind=kind,
                file_path=path,
                line_start=line_start,
                line_end=line_start,
                signature=sig,
            )
        )
    calls = {
        name
        for name in _GO_CALL_RE.findall(text)
        if name not in {"if", "for", "switch", "func", "return"}
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


def _parse_rust(path: str, language: str, size_bytes: int, text: str) -> SourceFile:
    imports = {m.group(1).strip() for m in _RUST_USE_RE.finditer(text)}
    symbols: list[Symbol] = []
    for regex, kind in [
        (_RUST_FN_RE, "function"),
        (_RUST_STRUCT_RE, "class"),
        (_RUST_ENUM_RE, "class"),
        (_RUST_TRAIT_RE, "class"),
        (_RUST_MOD_RE, "module"),
    ]:
        for match in regex.finditer(text):
            name = match.group("name")
            line_start = text.count("\n", 0, match.start()) + 1
            sig = text[match.start() : text.find("\n", match.start())].strip()
            symbols.append(
                Symbol(
                    name=name,
                    kind=kind,
                    file_path=path,
                    line_start=line_start,
                    line_end=line_start,
                    signature=sig,
                )
            )
    calls = {
        name
        for name in _RUST_CALL_RE.findall(text)
        if name not in {"if", "for", "while", "loop", "match"}
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


def _parse_php(path: str, language: str, size_bytes: int, text: str) -> SourceFile:
    imports: set[str] = set()
    for m in _PHP_USE_RE.finditer(text):
        imports.add(m.group(1).strip())
    for m in _PHP_NAMESPACE_RE.finditer(text):
        imports.add(m.group(1).strip())
    symbols: list[Symbol] = []
    for regex, kind in [
        (_PHP_CLASS_RE, "class"),
        (_PHP_INTERFACE_RE, "class"),
        (_PHP_TRAIT_RE, "class"),
        (_PHP_FUNC_RE, "function"),
    ]:
        for match in regex.finditer(text):
            name = match.group("name")
            line_start = text.count("\n", 0, match.start()) + 1
            sig = text[match.start() : text.find("\n", match.start())].strip()
            symbols.append(
                Symbol(
                    name=name,
                    kind=kind,
                    file_path=path,
                    line_start=line_start,
                    line_end=line_start,
                    signature=sig,
                )
            )
    calls = {
        name
        for name in _PHP_CALL_RE.findall(text)
        if name not in {"if", "for", "while", "switch", "function"}
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
