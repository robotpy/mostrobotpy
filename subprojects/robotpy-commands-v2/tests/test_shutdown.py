import commands2
import hal
from util import Counter


def test_run_command(scheduler: commands2.CommandScheduler):
    counter = Counter()
    cmd = commands2.RunCommand(counter.increment)

    scheduler.schedule(cmd)
    scheduler.run()
    assert counter.value == 1

    hal.shutdown()

    scheduler.run()
    assert counter.value == 1
