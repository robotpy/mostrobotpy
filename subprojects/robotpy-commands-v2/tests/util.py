import commands2
from wpilib.simulation import DriverStationSim, pauseTiming, resumeTiming, stepTiming

# from unittest.mock import MagicMock


class ManualSimTime:
    def __enter__(self) -> "ManualSimTime":
        pauseTiming()
        return self

    def __exit__(self, *args):
        resumeTiming()

    def step(self, delta: float):
        stepTiming(delta)


class CommandTestHelper:
    def __init__(self) -> None:
        self.scheduler = commands2.CommandScheduler.getInstance()

    def __enter__(self):
        commands2.CommandScheduler.resetInstance()
        DriverStationSim.setEnabled(True)
        return self

    def __exit__(self, *args):
        pass


class Counter:
    def __init__(self) -> None:
        self.value = 0

    def increment(self):
        self.value += 1


class ConditionHolder:
    def __init__(self, cond: bool = False) -> None:
        self.cond = cond

    def getCondition(self) -> bool:
        return self.cond

    def setTrue(self):
        self.cond = True


class TestSubsystem(commands2.SubsystemBase):
    pass
