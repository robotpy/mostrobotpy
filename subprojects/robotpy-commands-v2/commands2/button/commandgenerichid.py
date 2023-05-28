from typing import Optional

from wpilib.event import EventLoop
from wpilib.interfaces import GenericHID

from ..commandscheduler import CommandScheduler
from .trigger import Trigger


class CommandGenericHID:
    """
    A version of GenericHID with Trigger factories for command-based.
    """

    def __init__(self, port: int):
        """
        Construct an instance of a device.

        :param port: The port on the Driver Station that the device is plugged into.
        """
        self._hid = GenericHID(port)

    def getHID(self) -> GenericHID:
        """
        Get the underlying GenericHID object.
        """
        return self._hid

    def button(self, button: int, loop: Optional[EventLoop] = None) -> Trigger:
        """
        Constructs an event instance around this button's digital signal.

        :param button: The button index
        :param loop: the event loop instance to attache the event to.
        """
        if loop is None:
            loop = CommandScheduler.getInstance().getDefaultButtonLoop()
        return Trigger(loop, lambda: self._hid.getRawButtonPressed(button))

    def pov(
        self, angle: int, *, pov: int = 0, loop: Optional[EventLoop] = None
    ) -> Trigger:
        """
        Constructs a Trigger instance based around this angle of a POV on the HID.

        The POV angles start at 0 in the up direction, and increase clockwise (e.g. right is 90,
        upper-left is 315).

        :param angle: POV angle in degrees, or -1 for the center / not pressed.
        :param pov: index of the POV to read (starting at 0). Defaults to 0.
        :param loop: the event loop instance to attach the event to. Defaults to {@link
            CommandScheduler#getDefaultButtonLoop() the default command scheduler button loop}.
        :returns: a Trigger instance based around this angle of a POV on the HID.
        """
        if loop is None:
            loop = CommandScheduler.getInstance().getDefaultButtonLoop()
        return Trigger(loop, lambda: self._hid.getPOV(pov) == angle)

    def povUp(self) -> Trigger:
        """
        Constructs a Trigger instance based around the 0 degree angle (up) of the default (index 0) POV
        on the HID, attached to {@link CommandScheduler#getDefaultButtonLoop() the default command
        scheduler button loop}.

        :returns: a Trigger instance based around the 0 degree angle of a POV on the HID.
        """
        return self.pov(0)

    def povUpRight(self) -> Trigger:
        """
        Constructs a Trigger instance based around the 45 degree angle (right up) of the default (index
        0) POV on the HID, attached to {@link CommandScheduler#getDefaultButtonLoop() the default
        command scheduler button loop}.

        :returns: a Trigger instance based around the 45 degree angle of a POV on the HID.
        """
        return self.pov(45)

    def povRight(self) -> Trigger:
        """
        Constructs a Trigger instance based around the 90 degree angle (right) of the default (index 0)
        POV on the HID, attached to {@link CommandScheduler#getDefaultButtonLoop() the default command
        scheduler button loop}.

        :returns: a Trigger instance based around the 90 degree angle of a POV on the HID.
        """
        return self.pov(90)

    def povDownRight(self) -> Trigger:
        """
        Constructs a Trigger instance based around the 135 degree angle (right down) of the default
        (index 0) POV on the HID, attached to {@link CommandScheduler#getDefaultButtonLoop() the
        default command scheduler button loop}.

        :returns: a Trigger instance based around the 135 degree angle of a POV on the HID.
        """
        return self.pov(135)

    def povDown(self) -> Trigger:
        """
        Constructs a Trigger instance based around the 180 degree angle (down) of the default (index 0)
        POV on the HID, attached to {@link CommandScheduler#getDefaultButtonLoop() the default command
        scheduler button loop}.

        :returns: a Trigger instance based around the 180 degree angle of a POV on the HID.
        """
        return self.pov(180)

    def povDownLeft(self) -> Trigger:
        """
        Constructs a Trigger instance based around the 225 degree angle (down left) of the default
        (index 0) POV on the HID, attached to {@link CommandScheduler#getDefaultButtonLoop() the
        default command scheduler button loop}.

        :returns: a Trigger instance based around the 225 degree angle of a POV on the HID.
        """
        return self.pov(225)

    def povLeft(self) -> Trigger:
        """
        Constructs a Trigger instance based around the 270 degree angle (left) of the default (index 0)
        POV on the HID, attached to {@link CommandScheduler#getDefaultButtonLoop() the default command
        scheduler button loop}.

        :returns: a Trigger instance based around the 270 degree angle of a POV on the HID.
        """
        return self.pov(270)

    def povUpLeft(self) -> Trigger:
        """
        Constructs a Trigger instance based around the 315 degree angle (left up) of the default (index
        0) POV on the HID, attached to {@link CommandScheduler#getDefaultButtonLoop() the default
        command scheduler button loop}.

        :returns: a Trigger instance based around the 315 degree angle of a POV on the HID.
        """
        return self.pov(315)

    def povCenter(self) -> Trigger:
        """
        Constructs a Trigger instance based around the center (not pressed) position of the default
        (index 0) POV on the HID, attached to {@link CommandScheduler#getDefaultButtonLoop() the
        default command scheduler button loop}.

        :returns: a Trigger instance based around the center position of a POV on the HID.
        """
        return self.pov(-1)

    def axisLessThan(
        self, axis: int, threshold: float, loop: Optional[EventLoop] = None
    ) -> Trigger:
        """
        Constructs a Trigger instance that is true when the axis value is less than {@code threshold},
        attached to the given loop.

        :param axis: The axis to read, starting at 0
        :param threshold: The value below which this trigger should return true.
        :param loop: the event loop instance to attach the trigger to
        :returns: a Trigger instance that is true when the axis value is less than the provided
            threshold.
        """
        if loop is None:
            loop = CommandScheduler.getInstance().getDefaultButtonLoop()
        return Trigger(loop, lambda: self._hid.getRawAxis(axis) < threshold)

    def axisGreaterThan(
        self, axis: int, threshold: float, loop: Optional[EventLoop] = None
    ) -> Trigger:
        """
        Constructs a Trigger instance that is true when the axis value is greater than {@code
        threshold}, attached to the given loop.

        :param axis: The axis to read, starting at 0
        :param threshold: The value above which this trigger should return true.
        :param loop: the event loop instance to attach the trigger to.
        :returns: a Trigger instance that is true when the axis value is greater than the provided
            threshold.
        """
        if loop is None:
            loop = CommandScheduler.getInstance().getDefaultButtonLoop()
        return Trigger(loop, lambda: self._hid.getRawAxis(axis) > threshold)

    def getRawAxis(self, axis: int) -> float:
        """
        Get the value of the axis.

        :param axis: The axis to read, starting at 0.
        :returns: The value of the axis.
        """
        return self._hid.getRawAxis(axis)
