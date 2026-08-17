from collections.abc import Callable
from typing import Optional, TypeVar, overload

from hal import RobotMode
from wpiutil import Color

__all__ = ["OpModeRobot", "autonomous", "teleop", "utility"]

from ._impl import opmode as _opmode
from ._wpilib import OpModeRobotBase, OpMode

_OpModeT = TypeVar("_OpModeT", bound=OpMode)


def _apply_opmode_decorator(
    cls: type[_OpModeT] | None,
    *,
    mode: RobotMode,
    name: str,
    group: str,
    description: str,
    text_color: Color | None,
    background_color: Color | None,
) -> type[_OpModeT] | Callable[[type[_OpModeT]], type[_OpModeT]]:
    def apply(opmode_cls: type[_OpModeT]) -> type[_OpModeT]:
        return _opmode.attach_metadata(
            opmode_cls,
            mode=mode,
            name=name,
            group=group,
            description=description,
            text_color=text_color,
            background_color=background_color,
        )

    return apply if cls is None else apply(cls)


@overload
def autonomous(
    cls: type[_OpModeT],
    *,
    name: str = "",
    group: str = "",
    description: str = "",
    text_color: Color | None = None,
    background_color: Color | None = None,
) -> type[_OpModeT]: ...


@overload
def autonomous(
    cls: None = None,
    *,
    name: str = "",
    group: str = "",
    description: str = "",
    text_color: Color | None = None,
    background_color: Color | None = None,
) -> Callable[[type[_OpModeT]], type[_OpModeT]]: ...


def autonomous(
    cls: type[_OpModeT] | None = None,
    *,
    name: str = "",
    group: str = "",
    description: str = "",
    text_color: Color | None = None,
    background_color: Color | None = None,
) -> type[_OpModeT] | Callable[[type[_OpModeT]], type[_OpModeT]]:
    """Mark an OpMode subclass for autonomous automatic registration.

    Use this decorator bare (``@autonomous``) or configured
    (``@autonomous(name=..., group=...)``). The optional description and colors
    are published with the Driver Station option.
    """
    return _apply_opmode_decorator(
        cls,
        mode=RobotMode.AUTONOMOUS,
        name=name,
        group=group,
        description=description,
        text_color=text_color,
        background_color=background_color,
    )


@overload
def teleop(
    cls: type[_OpModeT],
    *,
    name: str = "",
    group: str = "",
    description: str = "",
    text_color: Color | None = None,
    background_color: Color | None = None,
) -> type[_OpModeT]: ...


@overload
def teleop(
    cls: None = None,
    *,
    name: str = "",
    group: str = "",
    description: str = "",
    text_color: Color | None = None,
    background_color: Color | None = None,
) -> Callable[[type[_OpModeT]], type[_OpModeT]]: ...


def teleop(
    cls: type[_OpModeT] | None = None,
    *,
    name: str = "",
    group: str = "",
    description: str = "",
    text_color: Color | None = None,
    background_color: Color | None = None,
) -> type[_OpModeT] | Callable[[type[_OpModeT]], type[_OpModeT]]:
    """Mark an OpMode subclass for teleoperated automatic registration.

    Use this decorator bare (``@teleop``) or configured
    (``@teleop(name=..., group=...)``). The optional description and colors are
    published with the Driver Station option.
    """
    return _apply_opmode_decorator(
        cls,
        mode=RobotMode.TELEOPERATED,
        name=name,
        group=group,
        description=description,
        text_color=text_color,
        background_color=background_color,
    )


@overload
def utility(
    cls: type[_OpModeT],
    *,
    name: str = "",
    group: str = "",
    description: str = "",
    text_color: Color | None = None,
    background_color: Color | None = None,
) -> type[_OpModeT]: ...


@overload
def utility(
    cls: None = None,
    *,
    name: str = "",
    group: str = "",
    description: str = "",
    text_color: Color | None = None,
    background_color: Color | None = None,
) -> Callable[[type[_OpModeT]], type[_OpModeT]]: ...


def utility(
    cls: type[_OpModeT] | None = None,
    *,
    name: str = "",
    group: str = "",
    description: str = "",
    text_color: Color | None = None,
    background_color: Color | None = None,
) -> type[_OpModeT] | Callable[[type[_OpModeT]], type[_OpModeT]]:
    """Mark an OpMode subclass for utility automatic registration.

    Use this decorator bare (``@utility``) or configured
    (``@utility(name=..., group=...)``). The optional description and colors are
    published with the Driver Station option.
    """
    return _apply_opmode_decorator(
        cls,
        mode=RobotMode.UTILITY,
        name=name,
        group=group,
        description=description,
        text_color=text_color,
        background_color=background_color,
    )


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
    """

    def __init__(self):
        super().__init__()
        _opmode.discover_and_register(self)

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
