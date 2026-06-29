from typing import TYPE_CHECKING

import commands2
from util import *  # type: ignore

if TYPE_CHECKING:
    from .util import *

import pytest


def test_command_in_multiple_groups():
    command_1 = commands2.Command()
    command_2 = commands2.Command()

    commands2.ParallelCommandGroup(command_1, command_2)
    with pytest.raises(commands2.IllegalCommandUse):
        commands2.ParallelCommandGroup(command_1, command_2)


def test_command_in_group_externally_scheduled(scheduler: commands2.CommandScheduler):
    command_1 = commands2.Command()
    command_2 = commands2.Command()

    commands2.ParallelCommandGroup(command_1, command_2)

    with pytest.raises(commands2.IllegalCommandUse):
        scheduler.schedule(command_1)


def test_redecorated_command_error(scheduler: commands2.CommandScheduler):
    command = commands2.InstantCommand()
    command.with_timeout(10).until(lambda: False)
    with pytest.raises(commands2.IllegalCommandUse):
        command.with_timeout(10)
    scheduler.remove_composed_command(command)
    command.with_timeout(10)
