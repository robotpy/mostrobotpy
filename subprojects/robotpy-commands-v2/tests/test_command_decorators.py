from util import ConditionHolder, ManualSimTime
import commands2


def test_with_timeout(scheduler: commands2.CommandScheduler):
    with ManualSimTime() as tm:

        cmd = commands2.WaitCommand(10)
        timeout = cmd.withTimeout(2)

        scheduler.schedule(timeout)
        scheduler.run()

        assert not scheduler.isScheduled(cmd)
        assert scheduler.isScheduled(timeout)

        tm.step(3)

        scheduler.run()
        assert not scheduler.isScheduled(timeout)


def test_with_interrupt(scheduler: commands2.CommandScheduler):

    cond = ConditionHolder()

    cmd = commands2.WaitCommand(10)
    timeout = cmd.withInterrupt(cond.getCondition)

    scheduler.schedule(timeout)
    scheduler.run()

    assert not scheduler.isScheduled(cmd)
    assert scheduler.isScheduled(timeout)

    cond.setTrue()

    scheduler.run()
    assert not scheduler.isScheduled(cmd)


def test_before_starting(scheduler: commands2.CommandScheduler):

    cond = ConditionHolder()

    cmd = commands2.InstantCommand().beforeStarting(cond.setTrue)

    scheduler.schedule(cmd)

    assert cond.getCondition()

    scheduler.run()
    scheduler.run()

    assert not scheduler.isScheduled(cmd)


def test_and_then_fn(scheduler: commands2.CommandScheduler):
    cond = ConditionHolder()

    cmd = commands2.InstantCommand().andThen(cond.setTrue)

    scheduler.schedule(cmd)

    assert not cond.getCondition()

    scheduler.run()
    scheduler.run()

    assert not scheduler.isScheduled(cmd)
    assert cond.getCondition()


def test_and_then_commands(scheduler: commands2.CommandScheduler):
    cond = ConditionHolder()

    cmd1 = commands2.InstantCommand()
    cmd2 = commands2.InstantCommand(cond.setTrue)

    scheduler.schedule(cmd1.andThen(cmd2))

    assert not cond.getCondition()

    scheduler.run()

    assert cond.getCondition()


def test_deadline_with(scheduler: commands2.CommandScheduler):
    cond = ConditionHolder()

    dictator = commands2.WaitUntilCommand(cond.getCondition)
    endsBefore = commands2.InstantCommand()
    endsAfter = commands2.WaitUntilCommand(lambda: False)

    group = dictator.deadlineWith(endsBefore, endsAfter)

    scheduler.schedule(group)
    scheduler.run()

    assert scheduler.isScheduled(group)

    cond.setTrue()
    scheduler.run()

    assert not scheduler.isScheduled(group)


def test_along_with(scheduler: commands2.CommandScheduler):
    cond = ConditionHolder(False)

    cmd1 = commands2.WaitUntilCommand(cond.getCondition)
    cmd2 = commands2.InstantCommand()

    group = cmd1.alongWith(cmd2)

    scheduler.schedule(group)
    scheduler.run()

    assert scheduler.isScheduled(group)

    cond.setTrue()
    scheduler.run()

    assert not scheduler.isScheduled(group)


def test_race_with(scheduler: commands2.CommandScheduler):
    cmd1 = commands2.WaitUntilCommand(lambda: False)
    cmd2 = commands2.InstantCommand()

    group = cmd1.raceWith(cmd2)

    scheduler.schedule(group)
    scheduler.run()

    assert not scheduler.isScheduled(group)


def test_perpetually(scheduler: commands2.CommandScheduler):

    cmd = commands2.InstantCommand().perpetually()

    scheduler.schedule(cmd)

    scheduler.run()
    scheduler.run()

    assert scheduler.isScheduled(cmd)
