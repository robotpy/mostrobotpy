import ast
import importlib
import inspect
from dataclasses import dataclass
from hal import RobotMode
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, overload
from wpiutil import Color

__all__ = ["OpModeRobot", "autonomous", "teleop", "utility"]

from ._wpilib import OpModeRobotBase, OpMode


@dataclass(frozen=True)
class _OpModeMetadata:
    mode: RobotMode
    name: str | None
    group: str | None
    description: str | None
    textColor: Color | None
    backgroundColor: Color | None


_OpModeType = TypeVar("_OpModeType", bound=type[OpMode])
_DECORATOR_NAMES = {"autonomous", "teleop", "utility"}
_SUPPORTED_CTOR_PARAM_NAMES = frozenset({"robot", "user_controls"})


def _attach_opmode_metadata(
    cls: _OpModeType,
    *,
    mode: RobotMode,
    name: str | None = None,
    group: str | None = None,
    description: str | None = None,
    textColor: Color | None = None,
    backgroundColor: Color | None = None,
) -> _OpModeType:
    if not issubclass(cls, OpMode):
        raise TypeError(
            f"Decorated class {cls.__module__}.{cls.__qualname__} must inherit from OpMode"
        )

    if hasattr(cls, "__wpilib_opmode_metadata__"):
        raise ValueError("multiple opmode decorators are not allowed")

    cls.__wpilib_opmode_metadata__ = _OpModeMetadata(
        mode=mode,
        name=name or cls.__name__,
        group=group,
        description=description,
        textColor=textColor,
        backgroundColor=backgroundColor,
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
    textColor: Color | None = None,
    backgroundColor: Color | None = None,
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
    ungrouped. ``description`` is optional. ``textColor`` and
    ``backgroundColor`` are optional display colors; both must be provided to
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
    textColor: Color | None = None,
    backgroundColor: Color | None = None,
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
    ungrouped. ``description`` is optional. ``textColor`` and
    ``backgroundColor`` are optional display colors; both must be provided to
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
    textColor: Color | None = None,
    backgroundColor: Color | None = None,
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
    ``description`` is optional. ``textColor`` and ``backgroundColor`` are
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


def _is_scannable_python_file(path: Path) -> bool:
    if path.suffix != ".py":
        return False
    if any(part.startswith(".") for part in path.parts):
        return False
    if "__pycache__" in path.parts:
        return False
    return True


def _iter_scan_files(root: Path):
    for path in root.iterdir():
        if path.is_file() and _is_scannable_python_file(path):
            yield path

    opmodes_dir = root / "opmodes"
    if not opmodes_dir.is_dir():
        return

    for path in opmodes_dir.rglob("*.py"):
        if _is_scannable_python_file(path):
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


def _resolve_opmode_constructor_kwargs(
    opmodeCls: type,
    robot: "OpModeRobot",
    user_controls: Any | None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    initializer = opmodeCls.__dict__.get("__init__")
    if initializer is None:
        return kwargs

    for parameter in list(inspect.signature(initializer).parameters.values())[1:]:
        if parameter.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            raise TypeError(
                f"{opmodeCls.__module__}.{opmodeCls.__qualname__} constructor cannot use *args or **kwargs"
            )

        if parameter.name not in _SUPPORTED_CTOR_PARAM_NAMES:
            raise TypeError(
                f"{opmodeCls.__module__}.{opmodeCls.__qualname__} uses unsupported constructor parameter name {parameter.name!r}; "
                "supported names are 'robot' and 'user_controls'"
            )

        if parameter.name == "robot":
            kwargs[parameter.name] = robot
        elif user_controls is not None:
            kwargs[parameter.name] = user_controls
        elif parameter.default is inspect.Parameter.empty:
            raise TypeError(
                f"{opmodeCls.__module__}.{opmodeCls.__qualname__} requires 'user_controls', "
                f"but {type(robot).__module__}.{type(robot).__qualname__} did not declare user_controls"
            )

    return kwargs


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
            metadata = getattr(value, "__wpilib_opmode_metadata__", None)
            if metadata is None or not inspect.isclass(value):
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
            robot.addOpMode(
                value,
                metadata.mode,
                name,
                group,
                description,
                metadata.textColor,
                metadata.backgroundColor,
            )

    robot.publishOpModes()


class OpModeRobot(OpModeRobotBase):
    """
    OpModeRobot implements the opmode-based robot program framework.

    The OpModeRobot class is intended to be subclassed by a user creating a robot
    program.

    Opmodes are constructed when selected on the driver station, and destroyed
    when the robot is disabled after being enabled or a different opmode is
    selected. When no opmode is selected, nonePeriodic() is called. The
    driverStationConnected() function is called the first time the driver station
    connects to the robot.

    Decorated opmodes are auto-discovered from a limited set of Python modules
    near the robot class: ``*.py`` files directly beside ``robot.py`` and
    ``opmodes/**/*.py`` recursively under an ``opmodes`` subpackage. Any class
    decorated with ``@autonomous``, ``@teleop``, or ``@utility`` in those files
    is imported, validated as an ``OpMode`` subclass, registered automatically,
    and then published to the Driver Station during robot initialization.
    Selection names must be unique within each robot mode.

    Robot subclasses may declare a framework-managed user controls object using
    the ``user_controls=...`` class keyword::

        from wpilib import DefaultUserControls

        class Robot(OpModeRobot, user_controls=DefaultUserControls):
            ...

    When declared, the controls class is instantiated once per robot and may be
    injected into opmode constructors by naming a parameter ``user_controls``.
    The robot instance may likewise be injected by naming a parameter ``robot``.
    Supported opmode constructor shapes therefore include::

        __init__(self)
        __init__(self, robot)
        __init__(self, user_controls)
        __init__(self, robot, user_controls)

    Injection is strict by parameter name: any other constructor parameter name
    is rejected with ``TypeError``.
    """

    __wpilib_user_controls_type__: type | None = None

    def __init_subclass__(cls, *, user_controls: type | None = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if user_controls is not None and not isinstance(user_controls, type):
            raise TypeError("user_controls must be a type")
        if user_controls is not None:
            cls.__wpilib_user_controls_type__ = user_controls

    def __init__(self):
        super().__init__()
        self._user_controls = self._make_user_controls_instance()
        _discover_decorated_opmodes(self)

    def _make_user_controls_instance(self):
        user_controls_type = type(self).__wpilib_user_controls_type__
        if user_controls_type is None:
            return None

        try:
            return user_controls_type()
        except TypeError as exc:
            raise TypeError(
                f"{type(self).__module__}.{type(self).__qualname__} declared user_controls={user_controls_type.__module__}.{user_controls_type.__qualname__}, "
                "but it could not be constructed without arguments"
            ) from exc

    def addOpMode(
        self,
        opmodeCls: type,
        mode: RobotMode,
        name: str,
        group: Optional[str] = None,
        description: Optional[str] = None,
        textColor: Optional[Color] = None,
        backgroundColor: Optional[Color] = None,
    ) -> None:
        """
        Adds an operating mode option. It's necessary to call PublishOpModes() to
        make the added modes visible to the driver station.

        The textColor and backgroundColor parameters are optional, but setting
        only one has no effect (if only one is provided, it will be ignored).

        :param opmodeCls: opmode class; must be a public, non-abstract subclass of OpMode
                          with constructor parameters named only 'robot' and/or
                          'user_controls'. These dependencies are injected by name.
                          Supported constructor forms are (), (robot),
                          (user_controls), and (robot, user_controls).
        :param mode: robot mode
        :param name: name of the operating mode
        :param group: group of the operating mode
        :param description: description of the operating mode
        :param textColor: text color
        :param backgroundColor: background color
        """

        constructor_kwargs = _resolve_opmode_constructor_kwargs(
            opmodeCls, self, self._user_controls
        )

        def makeOpModeInstance() -> OpMode:
            return opmodeCls(**constructor_kwargs)  # type: ignore[arg-type]

        if textColor is None or backgroundColor is None:
            self.addOpModeFactory(
                makeOpModeInstance, mode, name, group or "", description or ""
            )
        else:
            self.addOpModeFactory(
                makeOpModeInstance,
                mode,
                name,
                group or "",
                description or "",
                textColor,
                backgroundColor,
            )
