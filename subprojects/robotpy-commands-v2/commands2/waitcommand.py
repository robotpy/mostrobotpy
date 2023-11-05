from __future__ import annotations

from wpilib import Timer

from .command import Command
from .commandgroup import *


class WaitCommand(Command):
    """
    A command that does nothing but takes a specified amount of time to finish."""

    def __init__(self, seconds: float):
        """
        Creates a new WaitCommand. This command will do nothing, and end after the specified duration.

        :param seconds: the time to wait, in seconds"""
        super().__init__()
        self._duration = seconds
        self._timer = Timer()

    def initialize(self):
        self._timer.reset()
        self._timer.start()

    def end(self, interrupted: bool):
        self._timer.stop()

    def isFinished(self) -> bool:
        return self._timer.hasElapsed(self._duration)

    def runsWhenDisabled(self) -> bool:
        return True
