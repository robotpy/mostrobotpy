from typing import TYPE_CHECKING

import commands2
from compositiontestbase import MultiCompositionTestBase  # type: ignore
from util import *  # type: ignore

if TYPE_CHECKING:
    from .util import *
    from .compositiontestbase import MultiCompositionTestBase

import pytest


class TestSequentialCommandGroupComposition(MultiCompositionTestBase):
    def compose(self, *members: commands2.Command):
        return commands2.SequentialCommandGroup(*members)


def test_sequential_group_schedule(scheduler: commands2.CommandScheduler):
    command_1 = commands2.Command()
    command_2 = commands2.Command()

    start_spying_on(command_1)
    start_spying_on(command_2)

    group = commands2.SequentialCommandGroup(command_1, command_2)

    scheduler.schedule(group)

    verify(command_1).initialize()
    verify(command_2, never()).initialize()

    command_1.is_finished = lambda: True
    scheduler.run()

    verify(command_1).execute()
    verify(command_1).end(False)
    verify(command_2).initialize()
    verify(command_2, never()).execute()
    verify(command_2, never()).end(False)

    command_2.is_finished = lambda: True
    scheduler.run()

    verify(command_1).execute()
    verify(command_1).end(False)
    verify(command_2).execute()
    verify(command_2).end(False)

    assert not scheduler.is_scheduled(group)


def test_sequential_group_interrupt(scheduler: commands2.CommandScheduler):
    command_1 = commands2.Command()
    command_2 = commands2.Command()
    command_3 = commands2.Command()

    start_spying_on(command_1)
    start_spying_on(command_2)
    start_spying_on(command_3)

    group = commands2.SequentialCommandGroup(command_1, command_2, command_3)

    scheduler.schedule(group)

    command_1.is_finished = lambda: True
    scheduler.run()
    scheduler.cancel(group)
    scheduler.run()

    verify(command_1).execute()
    verify(command_1, never()).end(True)
    verify(command_1).end(False)
    verify(command_2, never()).execute()
    verify(command_2).end(True)
    verify(command_3, never()).initialize()
    verify(command_3, never()).execute()

    # assert command3.end.times_called == 0
    verify(command_3, never()).end(True)
    verify(command_3, never()).end(False)

    assert not scheduler.is_scheduled(group)


def test_not_scheduled_cancel(scheduler: commands2.CommandScheduler):
    command_1 = commands2.Command()
    command_2 = commands2.Command()

    group = commands2.SequentialCommandGroup(command_1, command_2)

    scheduler.cancel(group)


def test_sequential_group_requirement(scheduler: commands2.CommandScheduler):
    system1 = commands2.Subsystem()
    system2 = commands2.Subsystem()
    system3 = commands2.Subsystem()
    system4 = commands2.Subsystem()

    command_1 = commands2.InstantCommand()
    command_1.add_requirements(system1, system2)
    command_2 = commands2.InstantCommand()
    command_2.add_requirements(system3)
    command_3 = commands2.InstantCommand()
    command_3.add_requirements(system3, system4)

    group = commands2.SequentialCommandGroup(command_1, command_2)

    scheduler.schedule(group)
    scheduler.schedule(command_3)

    assert not scheduler.is_scheduled(group)
    assert scheduler.is_scheduled(command_3)
