from __future__ import annotations

import re

import libcst as cst
from libcst.metadata import MetadataWrapper, ParentNodeProvider

from .manifest import Manifest
from .names import is_dunder, is_probably_type_name

_CAMEL_RE = re.compile(r"[a-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*")


class _AuditVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def __init__(self, manifest: Manifest):
        self.allowed = {ignored.name for ignored in manifest.ignored}
        self.messages: list[str] = []

    def _check(self, name: str, context: str) -> None:
        if name in self.allowed or is_dunder(name) or is_probably_type_name(name):
            return
        if _CAMEL_RE.search(name):
            self.messages.append(f"{context}: remaining camelCase name {name!r}")

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
