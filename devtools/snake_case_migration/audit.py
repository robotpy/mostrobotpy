from __future__ import annotations

import re

import libcst as cst

from .manifest import Manifest
from .names import is_dunder, is_probably_type_name

_CAMEL_RE = re.compile(r"[a-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*")


class _AuditVisitor(cst.CSTVisitor):
    def __init__(self, manifest: Manifest):
        mapped = {mapping.old for mapping in manifest.mappings}
        ignored = {ignored.name for ignored in manifest.ignored}
        self.allowed = mapped | ignored
        self.messages: list[str] = []

    def _check(self, name: str, context: str) -> None:
        if name in self.allowed or is_dunder(name) or is_probably_type_name(name):
            return
        if _CAMEL_RE.search(name):
            self.messages.append(f"{context}: remaining camelCase name {name!r}")

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        self._check(node.name.value, "function")

    def visit_Attribute(self, node: cst.Attribute) -> None:
        self._check(node.attr.value, "attribute")

    def visit_Arg(self, node: cst.Arg) -> None:
        if node.keyword is not None:
            self._check(node.keyword.value, "keyword")


def audit_python_source(source: str, manifest: Manifest) -> list[str]:
    visitor = _AuditVisitor(manifest)
    cst.parse_module(source).visit(visitor)
    return visitor.messages
