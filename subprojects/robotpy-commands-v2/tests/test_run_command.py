import commands2
from util import Counter


def test_run_command(scheduler: commands2.CommandScheduler):
    counter = Counter()
    cmd = commands2.RunCommand(counter.increment)

    scheduler.schedule(cmd)
    scheduler.run()
    scheduler.run()
    scheduler.run()

    assert counter.value == 3
