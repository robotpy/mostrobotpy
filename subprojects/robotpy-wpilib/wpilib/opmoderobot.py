import ast
import importlib
import inspect
from dataclasses import dataclass
from hal import RobotMode
from pathlib import Path
from typing import Callable, Optional, TypeVar, overload
from wpiutil import Color

__all__ = ["OpModeRobot", "autonomous", "teleop", "utility"]

from ._wpilib import OpModeRobotBase, OpMode, RobotState


@dataclass(frozen=True)
class _OpModeMetadata:
    mode: RobotMode
    name: str | None
    group: str | None
    description: str | None
    text_color: Color | None
    background_color: Color | None


_OpModeType = TypeVar("_OpModeType", bound=type[OpMode])
_DECORATOR_NAMES = {"autonomous", "teleop", "utility"}


def _attach_opmode_metadata(
    cls: _OpModeType,
    *,
    mode: RobotMode,
    name: str | None = None,
    group: str | None = None,
    description: str | None = None,
    text_color: Color | None = None,
    background_color: Color | None = None,
) -> _OpModeType:
    if not issubclass(cls, OpMode):
        raise TypeError(
            f"Decorated class {cls.__module__}.{cls.__qualname__} must inherit from OpMode"
        )

    if "_wpilib_opmode_metadata" in cls.__dict__:
        raise ValueError("multiple opmode decorators are not allowed")

    cls._wpilib_opmode_metadata = _OpModeMetadata(
        mode=mode,
        name=name or cls.__name__,
        group=group,
        description=description,
        text_color=text_color,
        background_color=background_color,
    )
    return cls


def _make_opmode_decorator(mode: RobotMode, _cls=None, **kwargs):
    def decorator(cls: _OpModeType) -> _OpModeType:
        return _attach_opmode_metadata(cls, mode=mode, **kwargs)

    if _cls is None:
        return decorator
    return decorator(_cls)


@overload
def autonomous(cls: _OpModeType, /) -> _OpModeType: ...


@overload
def autonomous(
    cls: None = None,
    /,
    *,
    name: str | None = None,
    group: str | None = None,
    description: str | None = None,
    text_color: Color | None = None,
    background_color: Color | None = None,
) -> Callable[[_OpModeType], _OpModeType]: ...


def autonomous(_cls=None, **kwargs):
    """
    Decorator for automatic registration of autonomous opmode classes.

    May be used with or without arguments::

        @autonomous
        class DefaultAutoMode(PeriodicOpMode):
            ...

        @autonomous(name="Two Ball", group="Autos", description="Example")
        class TwoBallAuto(PeriodicOpMode):
            ...

    ``name`` is shown as the selection name in the Driver Station and must be
    unique across autonomous opmodes in the project. If omitted, the class name
    is used. ``group`` controls Driver Station grouping and defaults to
    ungrouped. ``description`` is optional. ``text_color`` and
    ``background_color`` are optional display colors; both must be provided to
    have an effect.
    """
    return _make_opmode_decorator(RobotMode.AUTONOMOUS, _cls, **kwargs)


@overload
def teleop(cls: _OpModeType, /) -> _OpModeType: ...


@overload
def teleop(
    cls: None = None,
    /,
    *,
    name: str | None = None,
    group: str | None = None,
    description: str | None = None,
    text_color: Color | None = None,
    background_color: Color | None = None,
) -> Callable[[_OpModeType], _OpModeType]: ...


def teleop(_cls=None, **kwargs):
    """
    Decorator for automatic registration of teleoperated opmode classes.

    May be used with or without arguments::

        @teleop
        class DefaultTeleMode(PeriodicOpMode):
            ...

        @teleop(name="Drive", group="Main")
        class DriveMode(PeriodicOpMode):
            ...

    ``name`` is shown as the selection name in the Driver Station and must be
    unique across teleoperated opmodes in the project. If omitted, the class
    name is used. ``group`` controls Driver Station grouping and defaults to
    ungrouped. ``description`` is optional. ``text_color`` and
    ``background_color`` are optional display colors; both must be provided to
    have an effect.
    """
    return _make_opmode_decorator(RobotMode.TELEOPERATED, _cls, **kwargs)


@overload
def utility(cls: _OpModeType, /) -> _OpModeType: ...


@overload
def utility(
    cls: None = None,
    /,
    *,
    name: str | None = None,
    group: str | None = None,
    description: str | None = None,
    text_color: Color | None = None,
    background_color: Color | None = None,
) -> Callable[[_OpModeType], _OpModeType]: ...


def utility(_cls=None, **kwargs):
    """
    Decorator for automatic registration of utility opmode classes.

    May be used with or without arguments::

        @utility
        class ServoTest(PeriodicOpMode):
            ...

        @utility(name="Servo Test", group="Mechanisms")
        class ServoTest(PeriodicOpMode):
            ...

    ``name`` is shown as the selection name in the Driver Station and must be
    unique across utility opmodes in the project. If omitted, the class name is
    used. ``group`` controls Driver Station grouping and defaults to ungrouped.
    ``description`` is optional. ``text_color`` and ``background_color`` are
    optional display colors; both must be provided to have an effect.
    """
    return _make_opmode_decorator(RobotMode.UTILITY, _cls, **kwargs)


def _decorator_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _contains_opmode_decorator(path: Path) -> bool:
    try:
        source = path.read_text()
        tree = ast.parse(source, filename=str(path))
    except Exception as exc:
        raise RuntimeError(
            f"Failed to parse opmode scan file {path.resolve()}: {exc}"
        ) from exc

    for stmt in tree.body:
        if not isinstance(stmt, ast.ClassDef):
            continue
        for decorator in stmt.decorator_list:
            if _decorator_name(decorator) in _DECORATOR_NAMES:
                return True
    return False


def _iter_scan_files(root: Path):
    for path in root.iterdir():
        if path.is_file() and path.suffix == ".py":
            yield path

    opmodes_dir = root / "opmodes"
    if not opmodes_dir.is_dir():
        return

    for path in opmodes_dir.rglob("*.py"):
        yield path


def _module_name_from_path(robot_module, scan_root: Path, path: Path) -> str:
    relative_path = path.relative_to(scan_root)
    parts = list(relative_path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()

    package = robot_module.__spec__.parent if robot_module.__spec__ is not None else ""
    if package:
        return ".".join([package, *parts]) if parts else package
    return ".".join(parts)


def _discover_decorated_opmodes(robot: "OpModeRobot") -> None:
    robot_module = inspect.getmodule(type(robot))
    if robot_module is None or getattr(robot_module, "__file__", None) is None:
        raise RuntimeError(
            f"Unable to resolve robot module source file for {type(robot).__module__}.{type(robot).__qualname__}"
        )

    scan_root = Path(robot_module.__file__).resolve().parent
    discovered: set[type] = set()
    registered_names: set[tuple[RobotMode, str]] = set()

    for path in _iter_scan_files(scan_root):
        if not _contains_opmode_decorator(path):
            continue

        module_name = _module_name_from_path(robot_module, scan_root, path)
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to import opmode discovery candidate {path.resolve()}: {exc}"
            ) from exc
        for value in vars(module).values():
            if not inspect.isclass(value):
                continue
            metadata = value.__dict__.get("_wpilib_opmode_metadata")
            if metadata is None:
                continue
            if value in discovered:
                continue
            if not issubclass(value, OpMode):
                raise TypeError(
                    f"Decorated class {value.__module__}.{value.__qualname__} must inherit from OpMode"
                )

            name = metadata.name or value.__name__
            group = metadata.group or ""
            description = metadata.description or ""
            registration_key = (metadata.mode, name)
            if registration_key in registered_names:
                raise ValueError(
                    f"duplicate opmode registration for mode {metadata.mode} and name {name!r}"
                )

            registered_names.add(registration_key)
            discovered.add(value)
            robot.add_opmode(
                value,
                metadata.mode,
                name,
                group,
                description,
                metadata.text_color,
                metadata.background_color,
            )

    RobotState.publish_opmodes()


class OpModeRobot(OpModeRobotBase):
    """
    OpModeRobot implements the opmode-based robot program framework.

    The OpModeRobot class is intended to be subclassed by a user creating a robot
    program.

    Opmodes are constructed when selected on the driver station, and destroyed
    when the robot is disabled after being enabled or a different opmode is
    selected. When no opmode is selected, none_periodic() is called. The
    driver_station_connected() function is called the first time the driver station
    connects to the robot.

    Decorated opmodes are auto-discovered from a limited set of Python modules
    near the robot class: ``*.py`` files directly beside ``robot.py`` and
    ``opmodes/**/*.py`` recursively under an ``opmodes`` subpackage. Any class
    decorated with ``@autonomous``, ``@teleop``, or ``@utility`` in those files
    is imported, validated as an ``OpMode`` subclass, registered automatically,
    and then published to the Driver Station during robot initialization.
    """

    def __init__(self):
        super().__init__()
        _discover_decorated_opmodes(self)

    def add_opmode(
        self,
        opmode_cls: type,
        mode: RobotMode,
        name: str,
        group: Optional[str] = None,
        description: Optional[str] = None,
        text_color: Optional[Color] = None,
        background_color: Optional[Color] = None,
    ) -> None:
        """
        Adds an operating mode option. It's necessary to call publish_opmodes() to
        make the added modes visible to the driver station.

        The text_color and background_color parameters are optional, but setting
        only one has no effect (if only one is provided, it will be ignored).

        :param opmode_cls: opmode class; must be a public, non-abstract subclass of OpMode
                          with a constructor that either takes no arguments or accepts a
                          single argument of this class's type (the latter is preferred).
        :param mode: robot mode
        :param name: name of the operating mode
        :param group: group of the operating mode
        :param description: description of the operating mode
        :param text_color: text color
        :param background_color: background color
        """

        def make_opmode_instance() -> OpMode:
            # Try to instantiate with robot argument first
            try:
                return opmode_cls(self)  # type: ignore
            except TypeError:
                # Fallback to no-argument constructor
                return opmode_cls()  # type: ignore

        if text_color is None or background_color is None:
            self.add_opmode_factory(
                make_opmode_instance, mode, name, group or "", description or ""
            )
        else:
            self.add_opmode_factory(
                make_opmode_instance,
                mode,
                name,
                group or "",
                description or "",
                text_color,
                background_color,
            )
