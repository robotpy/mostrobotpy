import pytest

import commands2
from wpilib.simulation import DriverStationSim


@pytest.fixture(autouse=True)
def scheduler():
    commands2.CommandScheduler.resetInstance()
    DriverStationSim.setEnabled(True)
    DriverStationSim.notifyNewData()
    return commands2.CommandScheduler.getInstance()
