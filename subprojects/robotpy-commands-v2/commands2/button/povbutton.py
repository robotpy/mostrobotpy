from wpilib.interfaces import GenericHID

from .trigger import Trigger


class POVButton(Trigger):
    """
    A Button that gets its state from a POV on a GenericHID.

    This class is provided by the NewCommands VendorDep
    """

    def __init__(self, joystick: GenericHID, angle: int, povNumber: int = 0):
        """
        Creates a POV button for triggering commands.

        :param joystick: The GenericHID object that has the POV
        :param angle: The desired angle in degrees (e.g. 90, 270)
        :param povNumber: The POV number (see GenericHID#getPOV(int))
        """
        super().__init__(lambda: joystick.getPOV(povNumber) == angle)
