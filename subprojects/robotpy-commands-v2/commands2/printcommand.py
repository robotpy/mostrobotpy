from __future__ import annotations

from .instantcommand import InstantCommand


class PrintCommand(InstantCommand):
    """
    A command that prints a string when initialized."""

    def __init__(self, message: str):
        """
        Creates a new a PrintCommand.

        :param message: the message to print"""
        super().__init__(lambda: print(message))

    def runsWhenDisabled(self) -> bool:
        return True
