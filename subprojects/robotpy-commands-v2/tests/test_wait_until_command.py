import commands2
from util import ConditionHolder


def test_wait_until(scheduler: commands2.CommandScheduler):
    cond = ConditionHolder()

    cmd = commands2.WaitUntilCommand(cond.getCondition)

    scheduler.schedule(cmd)
    scheduler.run()

    assert scheduler.isScheduled(cmd)
    cond.setTrue()

    scheduler.run()
    assert not scheduler.isScheduled(cmd)
