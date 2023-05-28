from __future__ import annotations

from typing import Set

from commands2.command import Command, InterruptionBehavior

from .command import Command, InterruptionBehavior
from .commandgroup import *
from .commandscheduler import CommandScheduler
from .util import flatten_args_commands


class ParallelRaceGroup(CommandGroup):
    """
    A composition that runs a set of commands in parallel, ending when any one of the commands ends
    and interrupting all the others.

    The rules for command compositions apply: command instances that are passed to it cannot be
    added to any other composition or scheduled individually, and the composition requires all
    subsystems its components require."""

    def __init__(self, *commands: Command):
        """
        Creates a new ParallelCommandRace. The given commands will be executed simultaneously, and will
        "race to the finish" - the first command to finish ends the entire command, with all other
        commands being interrupted.

        :param commands: the commands to include in this composition."""
        super().__init__()
        self._commands: Set[Command] = set()
        self._runsWhenDisabled = True
        self._interruptBehavior = InterruptionBehavior.kCancelIncoming
        self._finished = True
        self.addCommands(*commands)

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

            self._commands.add(command)
            self.requirements.update(command.getRequirements())
            self._runsWhenDisabled = (
                self._runsWhenDisabled and command.runsWhenDisabled()
            )

            if command.getInterruptionBehavior() == InterruptionBehavior.kCancelSelf:
                self._interruptBehavior = InterruptionBehavior.kCancelSelf

    def initialize(self):
        self._finished = False
        for command in self._commands:
            command.initialize()

    def execute(self):
        for command in self._commands:
            command.execute()
            if command.isFinished():
                self._finished = True

    def end(self, interrupted: bool):
        for command in self._commands:
            command.end(not command.isFinished())

    def isFinished(self) -> bool:
        return self._finished

    def runsWhenDisabled(self) -> bool:
        return self._runsWhenDisabled

    def getInterruptionBehavior(self) -> InterruptionBehavior:
        return self._interruptBehavior
