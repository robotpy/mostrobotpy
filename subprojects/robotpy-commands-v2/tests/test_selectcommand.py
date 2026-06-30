from typing import TYPE_CHECKING

import commands2
from compositiontestbase import MultiCompositionTestBase  # type: ignore
from util import *  # type: ignore

if TYPE_CHECKING:
    from .util import *
    from .compositiontestbase import MultiCompositionTestBase

import pytest


class TestSelectCommandComposition(MultiCompositionTestBase):
    def compose(self, *members: commands2.Command):
        return commands2.SelectCommand(dict(enumerate(members)), lambda: 0)


def test_select_command(scheduler: commands2.CommandScheduler):
    command_1 = commands2.Command()
    command_2 = commands2.Command()
    command_3 = commands2.Command()

    start_spying_on(command_1)
    start_spying_on(command_2)
    start_spying_on(command_3)

    command_1.is_finished = lambda: True

    select_command = commands2.SelectCommand(
        {"one": command_1, "two": command_2, "three": command_3}, lambda: "one"
    )

    scheduler.schedule(select_command)
    scheduler.run()

    verify(command_1).initialize()
    verify(command_1).execute()
    verify(command_1).end(False)

    verify(command_2, never()).initialize()
    verify(command_2, never()).execute()
    verify(command_2, never()).end(False)

    verify(command_3, never()).initialize()
    verify(command_3, never()).execute()
    verify(command_3, never()).end(False)


def test_select_command_invalid_key(scheduler: commands2.CommandScheduler):
    command_1 = commands2.Command()
    command_2 = commands2.Command()
    command_3 = commands2.Command()

    start_spying_on(command_1)
    start_spying_on(command_2)
    start_spying_on(command_3)

    command_1.is_finished = lambda: True

    select_command = commands2.SelectCommand(
        {"one": command_1, "two": command_2, "three": command_3}, lambda: "four"
    )

    scheduler.schedule(select_command)


def test_select_command_requirement(scheduler: commands2.CommandScheduler):
    system1 = commands2.Subsystem()
    system2 = commands2.Subsystem()
    system3 = commands2.Subsystem()
    system4 = commands2.Subsystem()

    command_1 = commands2.Command()
    command_1.add_requirements(system1, system2)
    command_2 = commands2.Command()
    command_2.add_requirements(system3)
    command_3 = commands2.Command()
    command_3.add_requirements(system3, system4)

    start_spying_on(command_1)
    start_spying_on(command_2)
    start_spying_on(command_3)

    select_command = commands2.SelectCommand(
        {"one": command_1, "two": command_2, "three": command_3}, lambda: "one"
    )

    scheduler.schedule(select_command)
    scheduler.schedule(commands2.InstantCommand(lambda: None, system3))

    verify(command_1).end(interrupted=True)
    verify(command_2, never()).end(interrupted=True)
    verify(command_3, never()).end(interrupted=True)
