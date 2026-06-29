from __future__ import annotations

import re
from pathlib import Path

import libcst as cst
from libcst.metadata import MetadataWrapper, ParentNodeProvider

from .manifest import Manifest
from .names import is_dunder, is_probably_type_name

_CAMEL_RE = re.compile(r"[a-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*")
_SEMIWRAP_DEF_RE = re.compile(
    r'\.(def(?:_static|_readwrite|_readonly|_property|_property_readonly)?)\s*\(\s*"([A-Za-z_][A-Za-z0-9_]*)"'
)
_SEMIWRAP_RENAME_RE = re.compile(r"^\s*rename:\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?:#.*)?$")
_AUDIT_SUFFIXES = {".py", ".pyi", ".yml", ".yaml"}


def iter_audit_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix in _AUDIT_SUFFIXES:
            files.append(path)
        elif path.is_dir():
            files.extend(
                p
                for p in path.rglob("*")
                if p.is_file()
                and p.suffix in _AUDIT_SUFFIXES
                and "__pycache__" not in p.parts
                and ".git" not in p.parts
            )
    return sorted(files)


class _AuditVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def __init__(self, manifest: Manifest):
        self.allowed = {ignored.name for ignored in manifest.ignored}
        self.mapped_old_names = {
            mapping.old: mapping.new
            for mapping in manifest.mappings
            if mapping.old != mapping.new
        }
        self.messages: list[str] = []

    def _check(self, name: str, context: str) -> None:
        if name in self.allowed or is_dunder(name):
            return
        if name in self.mapped_old_names:
            self.messages.append(
                f"{context}: mapped old name {name!r} remains; "
                f"expected {self.mapped_old_names[name]!r}"
            )
            return
        if _is_probably_type_like_public_name(name):
            return
        if _CAMEL_RE.search(name):
            self.messages.append(f"{context}: unmapped camelCase candidate {name!r}")

    def _name_is_checked_by_specific_visitor(self, node: cst.Name) -> bool:
        parent = self.get_metadata(ParentNodeProvider, node)
        return (
            (isinstance(parent, cst.FunctionDef) and parent.name is node)
            or (isinstance(parent, cst.Attribute) and parent.attr is node)
            or (isinstance(parent, cst.Arg) and parent.keyword is node)
            or (isinstance(parent, cst.Param) and parent.name is node)
        )

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        self._check(node.name.value, "function")

    def visit_Attribute(self, node: cst.Attribute) -> None:
        self._check(node.attr.value, "attribute")

    def visit_Arg(self, node: cst.Arg) -> None:
        if node.keyword is not None:
            self._check(node.keyword.value, "keyword")

    def visit_Param(self, node: cst.Param) -> None:
        self._check(node.name.value, "parameter")

    def visit_Name(self, node: cst.Name) -> None:
        if not self._name_is_checked_by_specific_visitor(node):
            self._check(node.value, "name")


def audit_python_source(source: str, manifest: Manifest) -> list[str]:
    visitor = _AuditVisitor(manifest)
    MetadataWrapper(cst.parse_module(source)).visit(visitor)
    return visitor.messages


def _is_probably_type_like_public_name(name: str) -> bool:
    stripped = name.lstrip("_")
    return bool(stripped) and is_probably_type_name(stripped)


def _check_public_output_name(
    name: str, context: str, manifest: Manifest, messages: list[str]
) -> None:
    if name in {ignored.name for ignored in manifest.ignored} or is_dunder(name):
        return
    mapped_old_names = {
        mapping.old: mapping.new for mapping in manifest.mappings if mapping.old != mapping.new
    }
    if name in mapped_old_names:
        messages.append(
            f"{context}: mapped old name {name!r} remains; "
            f"expected {mapped_old_names[name]!r}"
        )
        return
    if _is_probably_type_like_public_name(name):
        return
    if _CAMEL_RE.search(name):
        messages.append(f"{context}: unmapped camelCase candidate {name!r}")


def audit_semiwrap_yaml_source(source: str, manifest: Manifest) -> list[str]:
    messages: list[str] = []
    for lineno, line in enumerate(source.splitlines(), 1):
        def_match = _SEMIWRAP_DEF_RE.search(line)
        if def_match is not None:
            method, name = def_match.groups()
            _check_public_output_name(
                name, f"semiwrap .{method} line {lineno}", manifest, messages
            )
            continue

        rename_match = _SEMIWRAP_RENAME_RE.match(line)
        if rename_match is not None:
            name = rename_match.group(1)
            _check_public_output_name(
                name, f"semiwrap rename line {lineno}", manifest, messages
            )
    return messages
