from ._wpilib import Gamepad

__all__ = ["UserControls", "DefaultUserControls"]


class UserControls:
    """Marker base class for framework-managed user controls objects."""


class DefaultUserControls(UserControls):
    """Provides one Gamepad per standard driver station port."""

    def __init__(self):
        self._gamepads = tuple(Gamepad(port) for port in range(6))

    def getGamepad(self, port: int) -> Gamepad:
        """Return the Gamepad instance for the specified driver station port."""
        return self._gamepads[port]
