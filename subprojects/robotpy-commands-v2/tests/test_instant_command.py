import commands2
from util import ConditionHolder


def test_instant_command(scheduler: commands2.CommandScheduler):
    cond = ConditionHolder()

    cmd = commands2.InstantCommand(cond.setTrue)

    scheduler.schedule(cmd)
    scheduler.run()

    assert cond.getCondition()
    assert not scheduler.isScheduled(cmd)
