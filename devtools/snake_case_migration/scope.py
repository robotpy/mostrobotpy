from __future__ import annotations

import posixpath
from pathlib import Path

from .manifest import Ignore, Manifest, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _normalize_scope_path(path: str | Path) -> str:
    return posixpath.normpath(str(path).replace("\\", "/"))


def _candidate_roots(root_path: str | Path | None) -> list[Path]:
    roots: list[Path] = []
    if root_path is not None:
        roots.append(Path(root_path))
    roots.extend([_REPO_ROOT, Path.cwd()])
    return roots


def _normalize_absolute_manifest_path(
    path: Path, root_path: str | Path | None = None
) -> str | None:
    resolved_path = path.resolve()
    for root in _candidate_roots(root_path):
        try:
            return _normalize_scope_path(resolved_path.relative_to(root.resolve()))
        except ValueError:
            pass
    return None


def normalize_manifest_path(
    path: str | Path | None, root_path: str | Path | None = None
) -> str | None:
    if path is None:
        return None

    path_obj = Path(path)
    if path_obj.is_absolute():
        normalized_absolute = _normalize_absolute_manifest_path(path_obj, root_path)
        return normalized_absolute or _normalize_scope_path(path_obj.resolve())

    cwd_relative = _normalize_absolute_manifest_path(Path.cwd() / path_obj, root_path)
    if cwd_relative is not None:
        return cwd_relative

    return _normalize_scope_path(path_obj)


def scope_matches_path(
    scope: str, path: str | Path | None, root_path: str | Path | None = None
) -> bool:
    if scope == "global":
        return True

    normalized_path = normalize_manifest_path(path, root_path)
    if normalized_path is None:
        return False

    normalized_scope = normalize_manifest_path(scope, root_path)
    if normalized_scope is None:
        return False
    normalized_scope = normalized_scope.rstrip("/")
    return normalized_path == normalized_scope or normalized_path.startswith(
        f"{normalized_scope}/"
    )


def scoped_mappings(
    manifest: Manifest, path: str | Path | None, root_path: str | Path | None = None
) -> list[Mapping]:
    return [
        mapping
        for mapping in manifest.mappings
        if mapping.old != mapping.new
        and scope_matches_path(mapping.scope, path, root_path)
    ]


def scoped_ignored(
    manifest: Manifest, path: str | Path | None, root_path: str | Path | None = None
) -> list[Ignore]:
    return [
        ignored
        for ignored in manifest.ignored
        if scope_matches_path(ignored.scope, path, root_path)
    ]


def scoped_mapping_name_map(
    manifest: Manifest, path: str | Path | None, root_path: str | Path | None = None
) -> dict[str, str]:
    return {
        mapping.old: mapping.new
        for mapping in scoped_mappings(manifest, path, root_path)
    }


def scoped_ignored_names(
    manifest: Manifest, path: str | Path | None, root_path: str | Path | None = None
) -> set[str]:
    return {ignored.name for ignored in scoped_ignored(manifest, path, root_path)}
