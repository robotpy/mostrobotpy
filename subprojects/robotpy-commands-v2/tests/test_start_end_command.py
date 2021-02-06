from commands2 import StartEndCommand
from util import CommandTestHelper


class StartEnd:
    def __init__(self) -> None:
        self.counter = 0

    def start(self):
        self.counter += 1

    def end(self):
        self.counter += 1


def test_start_end():
    with CommandTestHelper() as helper:
        se = StartEnd()

        cmd = StartEndCommand(se.start, se.end, [])

        helper.scheduler.schedule(cmd)
        helper.scheduler.run()
        helper.scheduler.run()
        helper.scheduler.cancel(cmd)

        assert se.counter == 2
