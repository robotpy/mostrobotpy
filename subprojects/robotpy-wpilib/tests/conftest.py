import logging

import pytest
import ntcore
import wpilib


@pytest.fixture
def cfg_logging(caplog):
    caplog.set_level(logging.INFO)


@pytest.fixture(scope="function")
def nt(cfg_logging):
    instance = ntcore.NetworkTableInstance.getDefault()
    instance.startLocal()

    try:
        yield instance
    finally:
        instance.stopLocal()
        instance._reset()
        wpilib._wpilib._clearSmartDashboardData()
