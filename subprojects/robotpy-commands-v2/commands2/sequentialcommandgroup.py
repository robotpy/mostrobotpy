from __future__ import annotations

from typing import List

from commands2.command import Command, InterruptionBehavior

from .command import Command, InterruptionBehavior
from .commandgroup import *
from .commandscheduler import CommandScheduler
from .util import flatten_args_commands


class SequentialCommandGroup(CommandGroup):
    """
    A command composition that runs a list of commands in sequence.

    The rules for command compositions apply: command instances that are passed to it cannot be
    added to any other composition or scheduled individually, and the composition requires all
    subsystems its components require."""

    def __init__(self, *commands: Command):
        """
        Creates a new SequentialCommandGroup. The given commands will be run sequentially, with the
        composition finishing when the last command finishes.

        :param commands: the commands to include in this composition."""
        super().__init__()
        self._commands: List[Command] = []
        self._runsWhenDisabled = True
        self._interruptBehavior = InterruptionBehavior.kCancelIncoming
        self._currentCommandIndex = -1
        self.addCommands(*commands)

    def addCommands(self, *commands: Command):
        commands = flatten_args_commands(commands)
        if self._currentCommandIndex != -1:
            raise IllegalCommandUse(
                "Commands cannot be added to a composition while it is running"
            )

        CommandScheduler.getInstance().registerComposedCommands(commands)

        for command in commands:
            self._commands.append(command)
            self.requirements.update(command.getRequirements())
            self._runsWhenDisabled = (
                self._runsWhenDisabled and command.runsWhenDisabled()
            )
            if command.getInterruptionBehavior() == InterruptionBehavior.kCancelSelf:
                self._interruptBehavior = InterruptionBehavior.kCancelSelf

    def initialize(self):
        self._currentCommandIndex = 0
        if self._commands:
            self._commands[0].initialize()

    def execute(self):
        if not self._commands:
            return

        currentCommand = self._commands[self._currentCommandIndex]

        currentCommand.execute()
        if currentCommand.isFinished():
            currentCommand.end(False)
            self._currentCommandIndex += 1
            if self._currentCommandIndex < len(self._commands):
                self._commands[self._currentCommandIndex].initialize()

    def end(self, interrupted: bool):
        if not interrupted:
            return
        if not self._commands:
            return
        if not self._currentCommandIndex > -1:
            return
        if not self._currentCommandIndex < len(self._commands):
            return

        self._commands[self._currentCommandIndex].end(True)
        self._currentCommandIndex = -1

    def isFinished(self) -> bool:
        return self._currentCommandIndex == len(self._commands)

    def runsWhenDisabled(self) -> bool:
        return self._runsWhenDisabled

    def getInterruptionBehavior(self) -> InterruptionBehavior:
        return self._interruptBehavior
