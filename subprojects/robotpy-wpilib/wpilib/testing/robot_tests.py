"""
The primary purpose of these tests is to run through your code
and make sure that it doesn't crash. If you actually want to test
your code, you need to write your own custom tests to tease out
the edge cases.

To use these, add the following to a python file in your tests directory::

    from wpilib.testing.robot_tests import *

"""

import pytest

import wpilib
from hal._wpiHal import _RobotMode as RobotMode
from hal._wpiHal import opMode_GetRobotMode
from wpilib.simulation import DriverStationSim, stepTiming

from .controller import RobotTestController


def _step_timing_with_mode(
    control: RobotTestController,
    *,
    seconds: float,
    robot_mode: RobotMode,
    enabled: bool,
    assert_alive: bool = True,
    record_opmode_ids: set[int] | None = None,
) -> float:
    """Step simulation time while explicitly setting the robot mode."""

    assert control.robot_is_alive, "did you call control.run_robot()?"
    assert seconds > 0

    DriverStationSim.setDsAttached(True)
    DriverStationSim.setRobotMode(robot_mode)
    DriverStationSim.setEnabled(enabled)

    tm = 0.0
    while tm < seconds + 0.01:
        DriverStationSim.notifyNewData()
        stepTiming(0.2)
        if record_opmode_ids is not None:
            record_opmode_ids.add(wpilib.DriverStation.getOpModeId())
        if assert_alive:
            assert control.robot_is_alive
        tm += 0.2

    return tm


def test_autonomous(control: RobotTestController):
    """Runs autonomous mode by itself"""

    with control.run_robot():
        # Run disabled for a short period
        control.step_timing(seconds=0.5, autonomous=True, enabled=False)

        # Run enabled for 15 seconds
        control.step_timing(seconds=15, autonomous=True, enabled=True)

        # Disabled for another short period
        control.step_timing(seconds=0.5, autonomous=True, enabled=False)


@pytest.mark.filterwarnings("ignore")
def test_disabled(control: RobotTestController, robot):
    """Runs disabled mode by itself"""

    with control.run_robot():
        # Run disabled + autonomous for a short period
        control.step_timing(seconds=5, autonomous=True, enabled=False)

        # Run disabled + !autonomous for a short period
        control.step_timing(seconds=5, autonomous=False, enabled=False)


@pytest.mark.filterwarnings("ignore")
def test_operator_control(control: RobotTestController):
    """Runs operator control mode by itself"""

    with control.run_robot():
        # Run disabled for a short period
        control.step_timing(seconds=0.5, autonomous=False, enabled=False)

        # Run enabled for 15 seconds
        control.step_timing(seconds=15, autonomous=False, enabled=True)

        # Disabled for another short period
        control.step_timing(seconds=0.5, autonomous=False, enabled=False)


@pytest.mark.filterwarnings("ignore")
def test_practice(control: RobotTestController):
    """Runs through the entire span of a practice match"""

    with control.run_robot():
        # Run disabled for a short period
        control.step_timing(seconds=0.5, autonomous=True, enabled=False)

        # Run autonomous + enabled for 15 seconds
        control.step_timing(seconds=15, autonomous=True, enabled=True)

        # Disabled for another short period
        control.step_timing(seconds=0.5, autonomous=False, enabled=False)

        # Run teleop + enabled for 2 minutes
        control.step_timing(seconds=120, autonomous=False, enabled=True)


@pytest.mark.filterwarnings("ignore")
def test_all_opmodes(control: RobotTestController):
    """Runs each registered opmode briefly."""

    with control.run_robot():
        opmodes = DriverStationSim.getOpModeOptions()
        if len(opmodes) == 0:
            pytest.skip("robot did not register opmodes")

        selected = []
        seen = set()
        for opmode in reversed(opmodes):
            mode = opMode_GetRobotMode(opmode.id)
            if mode == RobotMode.UNKNOWN:
                continue
            key = (opmode.name, mode)
            if key in seen:
                continue
            seen.add(key)
            selected.append((opmode, mode))

        for opmode, mode in reversed(selected):
            DriverStationSim.setOpMode(opmode.id)

            _step_timing_with_mode(control, seconds=0.5, robot_mode=mode, enabled=False)
            opmode_ids = set()
            _step_timing_with_mode(
                control,
                seconds=2.0,
                robot_mode=mode,
                enabled=True,
                record_opmode_ids=opmode_ids,
            )
            _step_timing_with_mode(control, seconds=0.5, robot_mode=mode, enabled=False)
            assert (
                opmode.id in opmode_ids
            ), f"opmode {opmode.name} ({opmode.id}) did not run"
