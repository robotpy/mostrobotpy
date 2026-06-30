from __future__ import annotations

from pathlib import Path

import libcst as cst

from .manifest import Manifest
from .names import is_dunder, is_probably_type_name
from .scope import scoped_mappings


class _RenameTransformer(cst.CSTTransformer):
    def __init__(
        self,
        manifest: Manifest,
        path: str | Path | None = None,
        root_path: str | Path | None = None,
    ):
        mappings = scoped_mappings(manifest, path, root_path)
        self.name_map: dict[str, str] = {
            mapping.old: mapping.new for mapping in mappings
        }
        self.kind_map: dict[str, str] = {
            mapping.old: mapping.kind for mapping in mappings
        }

    def _rename(self, value: str) -> str:
        if is_dunder(value):
            return value
        if is_probably_type_name(value) and self.kind_map.get(value) not in {
            "attribute",
            "enum_value",
            "function",
            "method",
            "parameter",
        }:
            return value
        return self.name_map.get(value, value)

    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name) -> cst.Name:
        return updated_node.with_changes(value=self._rename(updated_node.value))

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        return updated_node.with_changes(name=original_node.name)

    def leave_Attribute(
        self, original_node: cst.Attribute, updated_node: cst.Attribute
    ) -> cst.Attribute:
        return updated_node.with_changes(
            attr=updated_node.attr.with_changes(
                value=self._rename(updated_node.attr.value)
            )
        )

    def leave_Param(
        self, original_node: cst.Param, updated_node: cst.Param
    ) -> cst.Param:
        return updated_node.with_changes(
            name=updated_node.name.with_changes(
                value=self._rename(updated_node.name.value)
            )
        )

    def leave_Arg(self, original_node: cst.Arg, updated_node: cst.Arg) -> cst.Arg:
        if updated_node.keyword is None:
            return updated_node
        return updated_node.with_changes(
            keyword=updated_node.keyword.with_changes(
                value=self._rename(updated_node.keyword.value)
            )
        )


def rewrite_python_source(
    source: str,
    manifest: Manifest,
    path: str | Path | None = None,
    root_path: str | Path | None = None,
) -> str:
    module = cst.parse_module(source)
    return module.visit(_RenameTransformer(manifest, path, root_path)).code
