from __future__ import annotations

import libcst as cst

from .manifest import Manifest


class _RenameTransformer(cst.CSTTransformer):
    def __init__(self, manifest: Manifest):
        self.name_map: dict[str, str] = {
            mapping.old: mapping.new
            for mapping in manifest.mappings
            if mapping.old != mapping.new
        }

    def _rename(self, value: str) -> str:
        return self.name_map.get(value, value)

    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name) -> cst.Name:
        return updated_node.with_changes(value=self._rename(updated_node.value))

    def leave_Attribute(
        self, original_node: cst.Attribute, updated_node: cst.Attribute
    ) -> cst.Attribute:
        return updated_node.with_changes(
            attr=updated_node.attr.with_changes(value=self._rename(updated_node.attr.value))
        )

    def leave_Param(self, original_node: cst.Param, updated_node: cst.Param) -> cst.Param:
        return updated_node.with_changes(
            name=updated_node.name.with_changes(value=self._rename(updated_node.name.value))
        )

    def leave_Arg(self, original_node: cst.Arg, updated_node: cst.Arg) -> cst.Arg:
        if updated_node.keyword is None:
            return updated_node
        return updated_node.with_changes(
            keyword=updated_node.keyword.with_changes(
                value=self._rename(updated_node.keyword.value)
            )
        )


def rewrite_python_source(source: str, manifest: Manifest) -> str:
    module = cst.parse_module(source)
    return module.visit(_RenameTransformer(manifest)).code
