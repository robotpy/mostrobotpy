from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from .audit import audit_python_source
from .manifest import Manifest, load_manifest, save_manifest
from .rewrite_py import rewrite_python_source


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

    subparsers.add_parser("pyproject", help="Apply semiwrap name_transform settings")
    subparsers.add_parser("scan-py", help="Scan Python files and update mappings")
    subparsers.add_parser("rewrite-py", help="Rewrite Python files using mappings")
    subparsers.add_parser("rewrite-text", help="Rewrite docs/examples text using mappings")
    subparsers.add_parser("audit", help="Report remaining old-style names")
    return parser


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

    return 0
