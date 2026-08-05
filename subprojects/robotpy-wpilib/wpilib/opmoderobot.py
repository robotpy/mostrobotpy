from hal import RobotMode
from typing import Optional
from wpiutil import Color

__all__ = ["OpModeRobot", "autonomous", "teleop", "utility"]

from ._impl import opmode as _opmode
from ._wpilib import OpModeRobotBase, OpMode


def _apply_opmode_decorator(cls, *, mode, **metadata):
    def apply(opmode_cls):
        return _opmode.attach_metadata(opmode_cls, mode=mode, **metadata)

    return apply if cls is None else apply(cls)


def autonomous(
    cls=None,
    *,
    name="",
    group="",
    description="",
    text_color=None,
    background_color=None,
):
    return _apply_opmode_decorator(
        cls,
        mode=RobotMode.AUTONOMOUS,
        name=name,
        group=group,
        description=description,
        text_color=text_color,
        background_color=background_color,
    )


def teleop(
    cls=None,
    *,
    name="",
    group="",
    description="",
    text_color=None,
    background_color=None,
):
    return _apply_opmode_decorator(
        cls,
        mode=RobotMode.TELEOPERATED,
        name=name,
        group=group,
        description=description,
        text_color=text_color,
        background_color=background_color,
    )


def utility(
    cls=None,
    *,
    name="",
    group="",
    description="",
    text_color=None,
    background_color=None,
):
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
