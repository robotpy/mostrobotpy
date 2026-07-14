import pathlib
import re
import sys
import typing as T

import click

from .ctx import Context

_STRUCT_SPECIALIZATION_RE = re.compile(
    r"\bstruct\b(?:(?!\{).)*?\bwpi::util::Struct\s*<\s*(.*?)\s*>",
    re.DOTALL,
)
_DEPENDENT_STRUCT_TYPE_WORDS = {
    "NumModules",
    "States",
    "Inputs",
    "Outputs",
    "Distance",
    "Rows",
    "Cols",
}


def _normalize_cpp_type(type_name: str) -> str:
    return " ".join(type_name.split())


def _find_struct_specializations(text: str) -> T.List[str]:
    """Find concrete wpi::util::Struct<T> specializations in C++ text."""
    types = []
    for match in _STRUCT_SPECIALIZATION_RE.finditer(text):
        type_name = _normalize_cpp_type(match.group(1))
        if not type_name:
            continue
        if "<" in type_name or ">" in type_name or "," in type_name:
            continue
        if any(word in type_name for word in _DEPENDENT_STRUCT_TYPE_WORDS):
            continue
        types.append(type_name)
    return types


def _struct_header_to_owner_header(
    header: pathlib.Path, include_root: pathlib.Path
) -> T.Optional[str]:
    """Map wpi/foo/struct/BarStruct.hpp to wpi/foo/Bar.hpp."""
    rel_parts = header.relative_to(include_root).parts
    if len(rel_parts) < 2 or rel_parts[-2] != "struct":
        return None

    name = rel_parts[-1]
    if not name.endswith("Struct.hpp"):
        return None

    owner_name = f"{name[:-len('Struct.hpp')]}.hpp"
    owner_parts = rel_parts[:-2] + (owner_name,)
    return pathlib.PurePosixPath(*owner_parts).as_posix()


def _has_setup_wpistruct(yaml_path: pathlib.Path, type_name: str) -> bool:
    text = yaml_path.read_text(encoding="utf-8")
    compact = re.sub(r"\s+", "", text)
    compact_type = re.sub(r"\s+", "", type_name)
    return f"SetupWPyStruct<{compact_type}>" in compact


def _native_include_roots(project) -> T.List[pathlib.Path]:
    native_root = project.path / "src" / "native"
    if not native_root.exists():
        return []
    return [p for p in native_root.glob("*/include") if p.is_dir()]


def _iter_native_headers(include_root: pathlib.Path) -> T.Iterator[pathlib.Path]:
    for header in include_root.rglob("*.h"):
        if header.is_file():
            yield header
    for header in include_root.rglob("*.hpp"):
        if header.is_file():
            yield header


def _collect_wpistruct_checks(
    ctx: Context,
) -> T.List[T.Tuple[str, pathlib.Path, str, pathlib.Path, bool]]:
    checks: T.List[T.Tuple[str, pathlib.Path, str, pathlib.Path, bool]] = []
    seen: T.Set[T.Tuple[str, pathlib.Path, str, pathlib.Path]] = set()

    for project in ctx.subprojects.values():
        if not getattr(project, "is_semiwrap_project", lambda: False)():
            continue

        semiwrap_cfg = project.pyproject_data["tool"]["semiwrap"]
        extension_modules = semiwrap_cfg.get("extension_modules", {})

        for module_cfg in extension_modules.values():
            headers = module_cfg.get("headers", {})
            if not headers:
                continue

            yaml_dir = project.path / module_cfg.get("yaml_path", "semiwrap")
            header_to_yaml = {
                header: yaml_dir / f"{name}.yml" for name, header in headers.items()
            }

            for native_name in module_cfg.get("wraps", []):
                native_project = ctx.subprojects.get(native_name)
                if native_project is None:
                    continue

                for include_root in _native_include_roots(native_project):
                    for struct_header in _iter_native_headers(include_root):
                        text = struct_header.read_text(
                            encoding="utf-8", errors="ignore"
                        )
                        if "wpi::util::Struct" not in text:
                            continue

                        direct_header = struct_header.relative_to(
                            include_root
                        ).as_posix()
                        owner_header = _struct_header_to_owner_header(
                            struct_header, include_root
                        )

                        yaml_path = header_to_yaml.get(direct_header)
                        if yaml_path is None and owner_header is not None:
                            yaml_path = header_to_yaml.get(owner_header)
                        if yaml_path is None:
                            continue

                        for type_name in _find_struct_specializations(text):
                            item = (project.name, yaml_path, type_name, struct_header)
                            if item in seen:
                                continue

                            seen.add(item)
                            checks.append(
                                (
                                    project.name,
                                    yaml_path,
                                    type_name,
                                    struct_header,
                                    yaml_path.exists()
                                    and _has_setup_wpistruct(yaml_path, type_name),
                                )
                            )

    return checks


def _collect_missing_wpistructs(
    ctx: Context,
) -> T.List[T.Tuple[str, pathlib.Path, str, pathlib.Path]]:
    return [
        (project_name, yaml_path, type_name, struct_header)
        for project_name, yaml_path, type_name, struct_header, found in _collect_wpistruct_checks(
            ctx
        )
        if not found
    ]


@click.command()
@click.pass_obj
def check_wpistructs(ctx: Context):
    """
    Ensures wrapped StructSerializable native types call SetupWPyStruct
    """
    checks = _collect_wpistruct_checks(ctx)
    missing = [
        (project_name, yaml_path, type_name, struct_header)
        for project_name, yaml_path, type_name, struct_header, found in checks
        if not found
    ]

    for _project_name, _yaml_path, type_name, _struct_header, found in checks:
        print(f"{type_name}: {'OK' if found else 'NOT FOUND'}")

    if not missing:
        return

    for project_name, yaml_path, type_name, struct_header in missing:
        print(
            f"ERROR: {project_name}: {type_name} is missing "
            f"SetupWPyStruct in {yaml_path} (struct specialization: {struct_header})",
            file=sys.stderr,
        )

    print(
        f"ERROR: {len(missing)} wrapped StructSerializable type(s) are missing "
        "SetupWPyStruct calls",
        file=sys.stderr,
    )
    sys.exit(1)
