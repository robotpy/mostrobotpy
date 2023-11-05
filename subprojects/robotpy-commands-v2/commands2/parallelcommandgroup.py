from __future__ import annotations

from typing import Dict

from commands2.command import Command, InterruptionBehavior

from .command import Command, InterruptionBehavior
from .commandgroup import *
from .commandscheduler import CommandScheduler
from .util import flatten_args_commands


class ParallelCommandGroup(CommandGroup):
    """
    A command composition that runs a set of commands in parallel, ending when the last command ends.

    The rules for command compositions apply: command instances that are passed to it cannot be
    added to any other composition or scheduled individually, and the composition requires all
    subsystems its components require."""

    def __init__(self, *commands: Command):
        """
        Creates a new ParallelCommandGroup. The given commands will be executed simultaneously. The
        command composition will finish when the last command finishes. If the composition is
        interrupted, only the commands that are still running will be interrupted.

        :param commands: the commands to include in this composition."""
        super().__init__()
        self._commands: Dict[Command, bool] = {}
        self._runsWhenDisabled = True
        self._interruptBehavior = InterruptionBehavior.kCancelIncoming
        self.addCommands(*commands)

    def addCommands(self, *commands: Command):
        commands = flatten_args_commands(commands)
        if True in self._commands.values():
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

    def execute(self):
        for command, isRunning in self._commands.items():
            if not isRunning:
                continue
            command.execute()
            if command.isFinished():
                command.end(False)
                self._commands[command] = False

    def end(self, interrupted: bool):
        if interrupted:
            for command, isRunning in self._commands.items():
                if not isRunning:
                    continue
                command.end(True)
                self._commands[command] = False

    def isFinished(self) -> bool:
        return True not in self._commands.values()

    def runsWhenDisabled(self) -> bool:
        return self._runsWhenDisabled

    def getInterruptionBehavior(self) -> InterruptionBehavior:
        return self._interruptBehavior
