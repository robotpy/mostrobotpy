from __future__ import annotations

import ast
from dataclasses import dataclass
import importlib
import inspect
from pathlib import Path
from typing import Any

from hal import RobotMode
from wpilib._wpilib import OpMode, RobotState

from .report_error import report_error


@dataclass(frozen=True)
class OpModeMetadata:
    mode: RobotMode
    name: str
    group: str
    description: str
    text_color: Any | None
    background_color: Any | None


_decorated_opmodes: list[type[OpMode]] = []


def attach_metadata(
    cls: type[OpMode],
    *,
    mode: RobotMode,
    name: str = "",
    group: str = "",
    description: str = "",
    text_color: Any | None = None,
    background_color: Any | None = None,
) -> type[OpMode]:
    if not inspect.isclass(cls) or not issubclass(cls, OpMode):
        raise TypeError("opmode decorator must be applied to an OpMode subclass")
    if "_wpilib_opmode_metadata" in cls.__dict__:
        raise ValueError("multiple opmode decorators are not allowed")

    cls._wpilib_opmode_metadata = OpModeMetadata(
        mode, name or cls.__name__, group, description, text_color, background_color
    )
    _decorated_opmodes.append(cls)
    return cls


def decorated_opmodes() -> tuple[type[OpMode], ...]:
    return tuple(_decorated_opmodes)


def _has_opmode_decorator(source: str, filename: str) -> bool:
    tree = ast.parse(source, filename=filename)
    decorator_names = {"autonomous", "teleop", "utility"}
    imported_decorators: set[str] = set()
    module_aliases: set[tuple[str, ...]] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for imported in node.names:
                if imported.name not in {"wpilib", "wpilib.opmoderobot"}:
                    continue
                if imported.asname is not None:
                    module_aliases.add((imported.asname,))
                else:
                    module_aliases.add(tuple(imported.name.split(".")))
        elif isinstance(node, ast.ImportFrom) and node.module in {
            "wpilib",
            "wpilib.opmoderobot",
        }:
            for imported in node.names:
                if node.module == "wpilib" and imported.name == "opmoderobot":
                    module_aliases.add((imported.asname or imported.name,))
                elif imported.name == "*":
                    imported_decorators.update(decorator_names)
                elif imported.name in decorator_names:
                    imported_decorators.add(imported.asname or imported.name)

    def attribute_path(node: ast.expr) -> tuple[str, ...] | None:
        parts: list[str] = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if not isinstance(node, ast.Name):
            return None
        parts.append(node.id)
        return tuple(reversed(parts))

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                decorator = decorator.func
            if isinstance(decorator, ast.Name):
                if decorator.id in imported_decorators:
                    return True
            elif isinstance(decorator, ast.Attribute):
                path = attribute_path(decorator)
                if (
                    path is not None
                    and path[-1] in decorator_names
                    and path[:-1] in module_aliases
                ):
                    return True
    return False


def _candidate_modules(package_dir: Path, package_name: str) -> list[str]:
    candidates: list[str] = []
    for source_path in sorted(package_dir.rglob("*.py")):
        try:
            has_opmode_decorator = _has_opmode_decorator(
                source_path.read_text(), str(source_path)
            )
        except SyntaxError as exc:
            report_error(f"Could not parse OpMode module {source_path}: {exc}")
            continue
        if not has_opmode_decorator:
            continue

        relative_path = source_path.relative_to(package_dir)
        if relative_path.name == "__init__.py":
            module_parts = relative_path.parent.parts
        else:
            module_parts = relative_path.with_suffix("").parts
        candidates.append(".".join((package_name, *module_parts)))
    return candidates


def _import_candidates(package_dir: Path, package_name: str) -> None:
    for module_name in _candidate_modules(package_dir, package_name):
        registry_length = len(_decorated_opmodes)
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            del _decorated_opmodes[registry_length:]
            report_error(
                f"Could not import OpMode module {module_name}: {exc}",
                print_trace=True,
            )


def _find_subclass(cls: type[OpMode]) -> type[OpMode] | None:
    subclasses = cls.__subclasses__()
    return subclasses[0] if subclasses else None


def discover_and_register(robot: Any) -> None:
    package_dir = Path(inspect.getfile(type(robot))).parent / "opmodes"
    if package_dir.is_dir() and (package_dir / "__init__.py").is_file():
        robot_module = type(robot).__module__
        robot_package = robot_module.rpartition(".")[0]
        package_name = f"{robot_package}.opmodes" if robot_package else "opmodes"
        _import_candidates(package_dir, package_name)

    registered: set[tuple[type[OpMode], RobotMode]] = set()
    registrations: list[tuple[type[OpMode], OpModeMetadata]] = []
    for cls in decorated_opmodes():
        metadata = cls.__dict__.get("_wpilib_opmode_metadata")
        if metadata is None or not issubclass(cls, OpMode):
            continue
        key = (cls, metadata.mode)
        if key in registered:
            continue
        registered.add(key)
        subclass = _find_subclass(cls)
        if subclass is not None:
            report_error(
                f"Decorated OpMode {cls.__qualname__} must not be subclassed; "
                f"found subclass {subclass.__qualname__}"
            )
            continue
        registrations.append((cls, metadata))

    for cls, metadata in registrations:
        robot.add_opmode(
            cls,
            metadata.mode,
            metadata.name,
            metadata.group,
            metadata.description,
            metadata.text_color,
            metadata.background_color,
        )
    RobotState.publish_opmodes()
