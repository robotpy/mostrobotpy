from __future__ import annotations

import ast
from pathlib import Path

from .manifest import Manifest, Mapping, merge_mapping
from .names import is_dunder, is_probably_type_name, to_snake_case


def iter_python_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend(
                p
                for p in path.rglob("*.py")
                if "__pycache__" not in p.parts and ".git" not in p.parts
            )
    return sorted(files)


def scan_python_file(path: Path, manifest: Manifest, scope: str) -> None:
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            if not is_dunder(name) and not is_probably_type_name(name):
                new = to_snake_case(name, "method")
                if new != name:
                    merge_mapping(
                        manifest,
                        Mapping(
                            kind="method",
                            old=name,
                            new=new,
                            source="scan-py",
                            scope=scope,
                        ),
                    )
        elif isinstance(node, ast.arg):
            name = node.arg
            if not is_dunder(name) and not is_probably_type_name(name):
                new = to_snake_case(name, "parameter")
                if new != name:
                    merge_mapping(
                        manifest,
                        Mapping(
                            kind="parameter",
                            old=name,
                            new=new,
                            source="scan-py",
                            scope=scope,
                        ),
                    )
