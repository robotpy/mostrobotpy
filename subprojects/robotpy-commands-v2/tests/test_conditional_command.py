from typing import TYPE_CHECKING

import commands2
from util import *  # type: ignore

if TYPE_CHECKING:
    from .util import *

import pytest


def test_conditional_command(scheduler: commands2.CommandScheduler):
    command_1 = commands2.Command()
    command_1.is_finished = lambda: True
    command_2 = commands2.Command()

    start_spying_on(command_1)
    start_spying_on(command_2)

    conditional_command = commands2.ConditionalCommand(command_1, command_2, lambda: True)

    scheduler.schedule(conditional_command)
    scheduler.run()

    verify(command_1).initialize()
    verify(command_1).execute()
    verify(command_1).end(False)

    verify(command_2, never()).initialize()
    verify(command_2, never()).execute()
    verify(command_2, never()).end(False)


def test_conditional_command_requirement(scheduler: commands2.CommandScheduler):
    system1 = commands2.Subsystem()
    system2 = commands2.Subsystem()
    system3 = commands2.Subsystem()

    command_1 = commands2.Command()
    command_1.add_requirements(system1, system2)
    command_2 = commands2.Command()
    command_2.add_requirements(system3)

    start_spying_on(command_1)
    start_spying_on(command_2)

    conditional_command = commands2.ConditionalCommand(command_1, command_2, lambda: True)

    scheduler.schedule(conditional_command)
    scheduler.schedule(commands2.InstantCommand(lambda: None, system3))

    assert not scheduler.is_scheduled(conditional_command)

    assert command_1.end.called_with(True)
    assert not command_2.end.called_with(True)
