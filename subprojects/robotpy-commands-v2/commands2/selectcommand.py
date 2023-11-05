from __future__ import annotations

from typing import Callable, Dict, Hashable

from commands2.command import InterruptionBehavior

from .command import Command, InterruptionBehavior
from .commandgroup import *
from .commandscheduler import CommandScheduler
from .printcommand import PrintCommand


class SelectCommand(Command):
    """
    A command composition that runs one of a selection of commands, either using a selector and a key
    to command mapping, or a supplier that returns the command directly at runtime.

    The rules for command compositions apply: command instances that are passed to it cannot be
    added to any other composition or scheduled individually, and the composition requires all
    subsystems its components require."""

    def __init__(
        self,
        commands: Dict[Hashable, Command],
        selector: Callable[[], Hashable],
    ):
        """
        Creates a new SelectCommand.

        :param commands: the map of commands to choose from
        :param selector: the selector to determine which command to run"""
        super().__init__()

        self._commands = commands
        self._selector = selector

        CommandScheduler.getInstance().registerComposedCommands(commands.values())

        self._runsWhenDisabled = True
        self._interruptBehavior = InterruptionBehavior.kCancelIncoming
        for command in commands.values():
            self.addRequirements(*command.getRequirements())
            self._runsWhenDisabled = (
                self._runsWhenDisabled and command.runsWhenDisabled()
            )
            if command.getInterruptionBehavior() == InterruptionBehavior.kCancelSelf:
                self._interruptBehavior = InterruptionBehavior.kCancelSelf

    def initialize(self):
        if self._selector() not in self._commands:
            self._selectedCommand = PrintCommand(
                "SelectCommand selector value does not correspond to any command!"
            )
            return
        self._selectedCommand = self._commands[self._selector()]
        self._selectedCommand.initialize()

    def execute(self):
        self._selectedCommand.execute()

    def end(self, interrupted: bool):
        self._selectedCommand.end(interrupted)

    def isFinished(self) -> bool:
        return self._selectedCommand.isFinished()

    def runsWhenDisabled(self) -> bool:
        return self._runsWhenDisabled

    def getInterruptionBehavior(self) -> InterruptionBehavior:
        return self._interruptBehavior
