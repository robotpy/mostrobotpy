from typing import TYPE_CHECKING

import commands2
from util import *  # type: ignore

if TYPE_CHECKING:
    from .util import *

import pytest


def test_schedule_command_schedule(scheduler: commands2.CommandScheduler):
    command_1 = commands2.Command()
    command_2 = commands2.Command()

    start_spying_on(command_1)
    start_spying_on(command_2)

    schedule_command = commands2.ScheduleCommand(command_1, command_2)

    scheduler.schedule(schedule_command)

    verify(command_1).schedule()
    verify(command_2).schedule()


def test_schedule_command_during_run(scheduler: commands2.CommandScheduler):
    to_schedule = commands2.InstantCommand()
    schedule_command = commands2.ScheduleCommand(to_schedule)
    group = commands2.SequentialCommandGroup(
        commands2.InstantCommand(), schedule_command
    )

    scheduler.schedule(group)
    scheduler.schedule(commands2.RunCommand(lambda: None))
    scheduler.run()
