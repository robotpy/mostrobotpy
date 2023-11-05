from __future__ import annotations

from .command import Command
from .commandgroup import *
from .commandscheduler import CommandScheduler


class PerpetualCommand(Command):
    """
    A command that runs another command in perpetuity, ignoring that command's end conditions. While
    this class does not extend CommandGroupBase, it is still considered a composition, as it
    allows one to compose another command within it; the command instances that are passed to it
    cannot be added to any other groups, or scheduled individually.

    As a rule, CommandGroups require the union of the requirements of their component commands.

    This class is provided by the NewCommands VendorDep

    @deprecated PerpetualCommand violates the assumption that execute() doesn't get called after
        isFinished() returns true -- an assumption that should be valid. This was unsafe/undefined
        behavior from the start, and RepeatCommand provides an easy way to achieve similar end
        results with slightly different (and safe) semantics."""

    def __init__(self, command: Command):
        """
        Creates a new PerpetualCommand. Will run another command in perpetuity, ignoring that command's
        end conditions, unless this command itself is interrupted.

        :param command: the command to run perpetually"""
        super().__init__()

        CommandScheduler.getInstance().registerComposedCommands([command])
        self._command = command
        self.addRequirements(*command.getRequirements())

    def initialize(self):
        self._command.initialize()

    def execute(self):
        self._command.execute

    def end(self, interrupted: bool):
        self._command.end(interrupted)

    def runsWhenDisabled(self) -> bool:
        return self._command.runsWhenDisabled()
