from wpilib.interfaces import GenericHID

from .trigger import Trigger


class JoystickButton(Trigger):
    """
    A Button that gets its state from a GenericHID.

    This class is provided by the NewCommands VendorDep
    """

    def __init__(self, joystick: GenericHID, buttonNumber: int):
        """
        Creates a joystick button for triggering commands.

        :param joystick: The GenericHID object that has the button (e.g. Joystick, KinectStick, etc)
        :param buttonNumber: The button number (see GenericHID#getRawButton(int)
        """
        super().__init__(lambda: joystick.getRawButton(buttonNumber))
