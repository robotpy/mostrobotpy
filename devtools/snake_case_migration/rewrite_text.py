from __future__ import annotations

from pathlib import Path

from .manifest import Manifest

TEXT_SUFFIXES = {".md", ".rst", ".py", ".toml", ".yml", ".yaml"}


def iter_text_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            files.append(path)
        elif path.is_dir():
            files.extend(
                p
                for p in path.rglob("*")
                if p.is_file()
                and p.suffix in TEXT_SUFFIXES
                and "__pycache__" not in p.parts
                and ".git" not in p.parts
            )
    return sorted(files)


def rewrite_text_source(source: str, manifest: Manifest) -> str:
    result = source
    for mapping in sorted(manifest.mappings, key=lambda m: len(m.old), reverse=True):
        if mapping.old != mapping.new:
            result = result.replace(mapping.old, mapping.new)
    return result
