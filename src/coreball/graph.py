"""Relationship analysis over repository models."""

from __future__ import annotations

from collections import defaultdict

from coreball.models import RepositoryModel


def build_symbol_index(model: RepositoryModel) -> dict[str, set[str]]:
    """Map symbol names to files that define them."""

    index: dict[str, set[str]] = defaultdict(set)
    for file in model.files:
        for symbol in file.symbols:
            index[symbol.name].add(file.path)
    return dict(index)


def related_files(model: RepositoryModel) -> dict[str, set[str]]:
    """Infer file-to-file relationships from imports and direct symbol calls."""

    symbol_index = build_symbol_index(model)
    by_stem = {file.path.rsplit(".", 1)[0].replace("/", "."): file.path for file in model.files}
    related: dict[str, set[str]] = {file.path: set() for file in model.files}

    for file in model.files:
        for imported in file.imports:
            normalized = imported.lstrip(".")
            if normalized in by_stem:
                related[file.path].add(by_stem[normalized])
            for module, target_path in by_stem.items():
                if normalized.endswith(module) or module.endswith(normalized):
                    related[file.path].add(target_path)
        for call in file.calls:
            for target_path in symbol_index.get(call, set()):
                if target_path != file.path:
                    related[file.path].add(target_path)
    return related
