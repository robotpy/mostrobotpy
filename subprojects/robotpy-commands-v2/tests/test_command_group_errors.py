import commands2
import pytest


def test_multiple_groups():
    cmd1 = commands2.InstantCommand()
    cmd2 = commands2.InstantCommand()

    _ = commands2.ParallelCommandGroup([cmd1, cmd2])
    with pytest.raises(RuntimeError):
        commands2.ParallelCommandGroup(cmd1, cmd2)


def test_externally_scheduled(scheduler: commands2.CommandScheduler):
    cmd1 = commands2.InstantCommand()
    cmd2 = commands2.InstantCommand()

    _ = commands2.SequentialCommandGroup([cmd1, cmd2])
    with pytest.raises(
        RuntimeError,
        match="A command that is part of a command group cannot be independently scheduled",
    ):
        scheduler.schedule(cmd1)


def test_redecorated():
    cmd = commands2.InstantCommand()

    _ = cmd.withTimeout(10).withInterrupt(lambda: False)

    with pytest.raises(RuntimeError):
        cmd.withTimeout(10)

    cmd.setGrouped(False)
    _ = cmd.withTimeout(10)
