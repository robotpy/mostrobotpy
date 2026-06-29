from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import tomlkit

from .audit import audit_python_source
from .manifest import Manifest, load_manifest, save_manifest
from .names import DEFAULT_ACRONYMS
from .rewrite_py import rewrite_python_source
from .rewrite_text import iter_text_files, rewrite_text_source
from .scan_py import iter_python_files, scan_python_file


def _add_write_paths(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--write", action="store_true", help="Write changes to disk")
    parser.add_argument("paths", nargs="+", type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snake_case_migration",
        description="Migrate semiwrap-based Python projects to snake_case APIs.",
    )
    parser.add_argument("--manifest", default="snake_case_migration.toml")
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest = subparsers.add_parser("manifest", help="Create or update manifest files")
    manifest_sub = manifest.add_subparsers(dest="manifest_command", required=True)
    manifest_sub.add_parser("init", help="Create a new manifest")
    manifest_sub.add_parser("check", help="Validate an existing manifest")

    pyproject = subparsers.add_parser(
        "pyproject", help="Apply semiwrap name_transform settings"
    )
    _add_write_paths(pyproject)

    scan_py = subparsers.add_parser(
        "scan-py", help="Scan Python files and update mappings"
    )
    _add_write_paths(scan_py)

    rewrite_py = subparsers.add_parser(
        "rewrite-py", help="Rewrite Python files using mappings"
    )
    _add_write_paths(rewrite_py)

    rewrite_text = subparsers.add_parser(
        "rewrite-text", help="Rewrite docs/examples text using mappings"
    )
    _add_write_paths(rewrite_text)

    audit = subparsers.add_parser("audit", help="Report remaining old-style names")
    audit.add_argument("paths", nargs="+", type=Path)
    return parser


def _load_or_new_manifest(path: Path) -> Manifest:
    if path.exists():
        return load_manifest(path)
    return Manifest()


def _ensure_table(parent: tomlkit.items.Table, key: str) -> tomlkit.items.Table:
    table = parent.get(key)
    if table is None:
        table = tomlkit.table()
        parent.add(key, table)
    return table


def _set_name_transform(semiwrap: tomlkit.items.Table) -> None:
    if semiwrap.get("name_transform") is None:
        semiwrap[tomlkit.key(["name_transform", "default"])] = "snake_case"
    name_transform = semiwrap["name_transform"]
    name_transform["default"] = "snake_case"
    name_transform["enum_value"] = "CAPS_CASE"
    name_transform["acronyms"] = list(DEFAULT_ACRONYMS)


def _run_pyproject(paths: list[Path], write: bool) -> int:
    changed: list[Path] = []
    for path in paths:
        original = path.read_text()
        doc = tomlkit.parse(original)
        tool = _ensure_table(doc, "tool")
        semiwrap = _ensure_table(tool, "semiwrap")
        _set_name_transform(semiwrap)
        updated = tomlkit.dumps(doc)
        if updated != original:
            changed.append(path)
            if write:
                path.write_text(updated)
    if not write:
        for path in changed:
            print(path)
    return 0


def _run_scan_py(paths: list[Path], manifest_path: Path, write: bool) -> int:
    manifest = _load_or_new_manifest(manifest_path)
    before = {
        (mapping.scope, mapping.kind, mapping.old, mapping.new)
        for mapping in manifest.mappings
    }
    for path in iter_python_files(paths):
        scan_python_file(path, manifest, str(path))
    after = {
        (mapping.scope, mapping.kind, mapping.old, mapping.new)
        for mapping in manifest.mappings
    }
    if write:
        save_manifest(manifest_path, manifest)
    else:
        for scope, kind, old, new in sorted(after - before):
            print(f"{scope}: {kind} {old} -> {new}")
    return 0


def _run_rewrite_py(paths: list[Path], manifest_path: Path, write: bool) -> int:
    manifest = load_manifest(manifest_path)
    changed: list[Path] = []
    for path in iter_python_files(paths):
        source = path.read_text()
        updated = rewrite_python_source(source, manifest)
        if updated != source:
            changed.append(path)
            if write:
                path.write_text(updated)
    if not write:
        for path in changed:
            print(path)
    return 0


def _run_rewrite_text(paths: list[Path], manifest_path: Path, write: bool) -> int:
    manifest = load_manifest(manifest_path)
    changed: list[Path] = []
    for path in iter_text_files(paths):
        source = path.read_text()
        updated = rewrite_text_source(source, manifest)
        if updated != source:
            changed.append(path)
            if write:
                path.write_text(updated)
    if not write:
        for path in changed:
            print(path)
    return 0


def _run_audit(paths: list[Path], manifest_path: Path) -> int:
    manifest = load_manifest(manifest_path)
    found = False
    for path in iter_python_files(paths):
        for message in audit_python_source(path.read_text(), manifest):
            print(f"{path}: {message}")
            found = True
    return 1 if found else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manifest_path = Path(args.manifest)

    if args.command == "manifest" and args.manifest_command == "init":
        if manifest_path.exists():
            load_manifest(manifest_path)
        else:
            save_manifest(manifest_path, Manifest())
        return 0

    if args.command == "manifest" and args.manifest_command == "check":
        load_manifest(manifest_path)
        return 0

    if args.command == "pyproject":
        return _run_pyproject(args.paths, args.write)

    if args.command == "scan-py":
        return _run_scan_py(args.paths, manifest_path, args.write)

    if args.command == "rewrite-py":
        return _run_rewrite_py(args.paths, manifest_path, args.write)

    if args.command == "rewrite-text":
        return _run_rewrite_text(args.paths, manifest_path, args.write)

    if args.command == "audit":
        return _run_audit(args.paths, manifest_path)

    return 0
