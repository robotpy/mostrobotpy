from __future__ import annotations

from typing import Callable

from .command import Command
from .commandgroup import *
from .commandscheduler import CommandScheduler


class ConditionalCommand(Command):
    """
    A command composition that runs one of two commands, depending on the value of the given
    condition when this command is initialized.

    The rules for command compositions apply: command instances that are passed to it cannot be
    added to any other composition or scheduled individually, and the composition requires all
    subsystems its components require.

    This class is provided by the NewCommands VendorDep"""

    selectedCommand: Command

    def __init__(
        self, onTrue: Command, onFalse: Command, condition: Callable[[], bool]
    ):
        """
        Creates a new ConditionalCommand.

        :param onTrue: the command to run if the condition is true
        :param onFalse: the command to run if the condition is false
        :param condition: the condition to determine which command to run"""
        super().__init__()

        CommandScheduler.getInstance().registerComposedCommands([onTrue, onFalse])

        self.onTrue = onTrue
        self.onFalse = onFalse
        self.condition = condition

        self.addRequirements(*onTrue.getRequirements())
        self.addRequirements(*onFalse.getRequirements())

    def initialize(self):
        if self.condition():
            self.selectedCommand = self.onTrue
        else:
            self.selectedCommand = self.onFalse

        self.selectedCommand.initialize()

    def execute(self):
        self.selectedCommand.execute()

    def isFinished(self) -> bool:
        return self.selectedCommand.isFinished()

    def end(self, interrupted: bool):
        self.selectedCommand.end(interrupted)

    def runsWhenDisabled(self) -> bool:
        return self.onTrue.runsWhenDisabled() and self.onFalse.runsWhenDisabled()
