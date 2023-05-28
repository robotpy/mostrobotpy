from __future__ import annotations

from .command import Command
from .commandgroup import *


class ProxyScheduleCommand(Command):
    """
    Schedules the given commands when this command is initialized, and ends when all the commands are
    no longer scheduled. Useful for forking off from CommandGroups. If this command is interrupted,
    it will cancel all the commands.
    """

    def __init__(self, *toSchedule: Command):
        """
        Creates a new ProxyScheduleCommand that schedules the given commands when initialized, and ends
        when they are all no longer scheduled.

        :param toSchedule: the commands to schedule
        @deprecated Replace with ProxyCommand, composing multiple of them in a {@link
            ParallelRaceGroup} if needed."""
        super().__init__()
        self.toSchedule = set(toSchedule)
        self._finished = False

    def initialize(self):
        for command in self.toSchedule:
            command.schedule()

    def end(self, interrupted: bool):
        if interrupted:
            for command in self.toSchedule:
                command.cancel()

    def execute(self):
        self._finished = True
        for command in self.toSchedule:
            self._finished = self._finished and not command.isScheduled()

    def isFinished(self) -> bool:
        return self._finished
