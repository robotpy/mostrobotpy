from __future__ import annotations

from typing import Dict

from commands2.command import Command, InterruptionBehavior

from .command import Command, InterruptionBehavior
from .commandgroup import *
from .commandscheduler import CommandScheduler
from .util import flatten_args_commands


class ParallelDeadlineGroup(CommandGroup):
    """
    A command composition that runs one of a selection of commands, either using a selector and a key
    to command mapping, or a supplier that returns the command directly at runtime.

    The rules for command compositions apply: command instances that are passed to it cannot be
    added to any other composition or scheduled individually, and the composition requires all
    subsystems its components require."""

    def __init__(self, deadline: Command, *commands: Command):
        """
        Creates a new SelectCommand.

        :param commands: the map of commands to choose from
        :param selector: the selector to determine which command to run"""
        super().__init__()
        self._commands: Dict[Command, bool] = {}
        self._runsWhenDisabled = True
        self._finished = True
        self._deadline = deadline
        self._interruptBehavior = InterruptionBehavior.kCancelIncoming
        self.addCommands(*commands)
        if deadline not in self._commands:
            self.addCommands(deadline)

    def setDeadline(self, deadline: Command):
        if deadline not in self._commands:
            self.addCommands(deadline)
        self._deadline = deadline

    def addCommands(self, *commands: Command):
        commands = flatten_args_commands(commands)
        if not self._finished:
            raise IllegalCommandUse(
                "Commands cannot be added to a composition while it is running"
            )

        CommandScheduler.getInstance().registerComposedCommands(commands)

        for command in commands:
            if not command.getRequirements().isdisjoint(self.requirements):
                raise IllegalCommandUse(
                    "Multiple comands in a parallel composition cannot require the same subsystems."
                )

            self._commands[command] = False
            self.requirements.update(command.getRequirements())
            self._runsWhenDisabled = (
                self._runsWhenDisabled and command.runsWhenDisabled()
            )

            if command.getInterruptionBehavior() == InterruptionBehavior.kCancelSelf:
                self._interruptBehavior = InterruptionBehavior.kCancelSelf

    def initialize(self):
        for command in self._commands:
            command.initialize()
            self._commands[command] = True
        self._finished = False

    def execute(self):
        for command, isRunning in self._commands.items():
            if not isRunning:
                continue
            command.execute()
            if command.isFinished():
                command.end(False)
                self._commands[command] = False
                if command == self._deadline:
                    self._finished = True

    def end(self, interrupted: bool):
        for command, isRunning in self._commands.items():
            if not isRunning:
                continue
            command.end(True)
            self._commands[command] = False

    def isFinished(self) -> bool:
        return self._finished

    def runsWhenDisabled(self) -> bool:
        return self._runsWhenDisabled

    def getInterruptionBehavior(self) -> InterruptionBehavior:
        return self._interruptBehavior
