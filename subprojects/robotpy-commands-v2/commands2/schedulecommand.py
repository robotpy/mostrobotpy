from __future__ import annotations

from .command import Command
from .commandgroup import *


class ScheduleCommand(Command):
    """
    Schedules the given commands when this command is initialized. Useful for forking off from
    CommandGroups. Note that if run from a composition, the composition will not know about the
    status of the scheduled commands, and will treat this command as finishing instantly.
    """

    def __init__(self, *commands: Command):
        """
        Creates a new ScheduleCommand that schedules the given commands when initialized.

        :param toSchedule: the commands to schedule"""
        super().__init__()
        self.toSchedule = set(commands)

    def initialize(self):
        for command in self.toSchedule:
            command.schedule()

    def isFinished(self) -> bool:
        return True

    def runsWhenDisabled(self) -> bool:
        return True
