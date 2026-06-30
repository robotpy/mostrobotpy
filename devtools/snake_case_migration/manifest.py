from __future__ import annotations

import dataclasses
from pathlib import Path

import tomlkit

from .names import DEFAULT_ACRONYMS


@dataclasses.dataclass(slots=True)
class Mapping:
    kind: str
    old: str
    new: str
    source: str
    scope: str = "global"
    reason: str = ""


@dataclasses.dataclass(slots=True)
class Ignore:
    name: str
    reason: str
    scope: str = "global"


@dataclasses.dataclass(slots=True)
class Manifest:
    acronyms: list[str] = dataclasses.field(default_factory=lambda: list(DEFAULT_ACRONYMS))
    mappings: list[Mapping] = dataclasses.field(default_factory=list)
    ignored: list[Ignore] = dataclasses.field(default_factory=list)
    semiwrap_bugs: list[dict[str, str]] = dataclasses.field(default_factory=list)


def _mapping_key(mapping: Mapping) -> tuple[str, str, str]:
    return (mapping.scope, mapping.kind, mapping.old)


def _semiwrap_bug_key(bug: dict[str, str]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted(bug.items()))


def merge_mapping(manifest: Manifest, mapping: Mapping) -> None:
    incoming_key = _mapping_key(mapping)
    for idx, existing in enumerate(manifest.mappings):
        if _mapping_key(existing) == incoming_key:
            if existing.source == "manual":
                return
            manifest.mappings[idx] = mapping
            return
    manifest.mappings.append(mapping)


def load_manifest(path: str | Path) -> Manifest:
    data = tomlkit.parse(Path(path).read_text())
    manifest = Manifest(acronyms=list(data.get("config", {}).get("acronyms", DEFAULT_ACRONYMS)))
    for item in data.get("mapping", []):
        manifest.mappings.append(Mapping(**dict(item)))
    for item in data.get("ignored", []):
        manifest.ignored.append(Ignore(**dict(item)))
    manifest.semiwrap_bugs = [dict(item) for item in data.get("semiwrap_bug", [])]
    return manifest


def save_manifest(path: str | Path, manifest: Manifest) -> None:
    doc = tomlkit.document()
    config = tomlkit.table()
    config.add("acronyms", sorted(dict.fromkeys(manifest.acronyms), key=str.casefold))
    doc.add("config", config)

    mappings = tomlkit.aot()
    for mapping in sorted(manifest.mappings, key=_mapping_key):
        item = tomlkit.table()
        for field in ("scope", "kind", "old", "new", "source", "reason"):
            value = getattr(mapping, field)
            if value:
                item.add(field, value)
        mappings.append(item)
    if mappings:
        doc.add("mapping", mappings)

    ignored_items = tomlkit.aot()
    for ignored in sorted(manifest.ignored, key=lambda i: (i.scope, i.name)):
        item = tomlkit.table()
        item.add("scope", ignored.scope)
        item.add("name", ignored.name)
        item.add("reason", ignored.reason)
        ignored_items.append(item)
    if ignored_items:
        doc.add("ignored", ignored_items)

    semiwrap_bugs = tomlkit.aot()
    for bug in sorted(manifest.semiwrap_bugs, key=_semiwrap_bug_key):
        item = tomlkit.table()
        for key in sorted(bug):
            item.add(key, bug[key])
        semiwrap_bugs.append(item)
    if semiwrap_bugs:
        doc.add("semiwrap_bug", semiwrap_bugs)

    Path(path).write_text(tomlkit.dumps(doc))
