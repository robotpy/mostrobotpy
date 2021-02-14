import commands2
from commands2 import WaitCommand

import pytest


class MySubsystem(commands2.SubsystemBase):
    def __init__(self, param) -> None:
        super().__init__()
        self.param = param


class MyCommand(commands2.CommandBase):
    def __init__(self, param) -> None:
        super().__init__()
        self.addRequirements(MySubsystem(param))


def get_params(g):
    return sorted(s.param for s in g.getRequirements())


@pytest.mark.parametrize(
    "ccls",
    [
        commands2.ParallelCommandGroup,
        lambda *args: commands2.ParallelDeadlineGroup(WaitCommand(1), *args),
        commands2.ParallelRaceGroup,
        commands2.SequentialCommandGroup,
    ],
)
def test_command_group_constructors(ccls):
    # individual param form
    g = ccls(MyCommand(1))
    assert get_params(g) == [1]

    g = ccls(MyCommand(1), MyCommand(2))
    assert get_params(g) == [1, 2]

    # list form
    g = ccls([MyCommand(1)])
    assert get_params(g) == [1]

    g = ccls([MyCommand(1), MyCommand(2)])
    assert get_params(g) == [1, 2]

    # tuple form
    g = ccls((MyCommand(1),))
    assert get_params(g) == [1]

    g = ccls((MyCommand(1), MyCommand(2)))
    assert get_params(g) == [1, 2]


@pytest.mark.parametrize(
    "ccls",
    [
        commands2.ParallelCommandGroup,
        lambda *args: commands2.ParallelDeadlineGroup(WaitCommand(1), *args),
        commands2.ParallelRaceGroup,
        commands2.SequentialCommandGroup,
    ],
)
def test_command_group_add_commands(ccls):
    g = ccls()

    # individual param form
    g.addCommands(WaitCommand(1))
    g.addCommands(WaitCommand(1), WaitCommand(2))

    # list form
    g.addCommands([WaitCommand(1)])
    g.addCommands([WaitCommand(1), WaitCommand(2)])

    # tuple form
