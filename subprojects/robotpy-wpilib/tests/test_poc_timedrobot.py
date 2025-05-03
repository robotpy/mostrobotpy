"""
Proof of concept to test TimedRobotPy using PyTest

This POC was made by deconstructing pytest_plugin.py so that it is no longer a plugin but a class that provides
fixtures.

To run / debug this:

pytest subprojects/robotpy-wpilib/tests/test_poc_timedrobot.py --no-header -vvv -s

"""

from pathlib import Path
import pytest

from wpilib.timedrobotpy import TimedRobotPy


from pyfrc.tests.basic import test_practice as _test_practice




class MyRobot(TimedRobotPy):
    def __init__(self):
        super().__init__(period=0.020)
        self.robotInitialized = False
        self.robotPeriodicCount = 0

    #########################################################
    ## Common init/update for all modes
    def robotInit(self):
        self.robotInitialized = True


    def robotPeriodic(self):
        self.robotPeriodicCount += 1

    #########################################################
    ## Autonomous-Specific init and update
    def autonomousInit(self):
        pass

    def autonomousPeriodic(self):
        pass

    def autonomousExit(self):
        pass


    #########################################################
    ## Teleop-Specific init and update
    def teleopInit(self):
        pass

    def teleopPeriodic(self):
        pass

    #########################################################
    ## Disabled-Specific init and update
    def disabledPeriodic(self):
        pass


    def disabledInit(self):
        pass

    #########################################################
    ## Test-Specific init and update
    def testInit(self):
        pass

    def testPeriodic(self):
        pass

import gc
import pathlib

from typing import Type

import pytest
import weakref

import hal
import hal.simulation
import ntcore
import wpilib
import wpilib.shuffleboard
from wpilib.simulation import DriverStationSim, pauseTiming, restartTiming
import wpilib.simulation

# TODO: get rid of special-casing.. maybe should register a HAL shutdown hook or something
try:
    import commands2
except ImportError:
    commands2 = None

from pyfrc.test_support.controller import TestController
from pyfrc.physics.core import PhysicsInterface

ROBOT_CLASS = MyRobot
ISOLATED = True
ROBOT_FILE = Path(__file__)

# attach physics
PHYSICS, ROBOT_CLASS = PhysicsInterface._create_and_attach(
    ROBOT_CLASS,
    ROBOT_FILE.parent,
)


# Tests need to know when robotInit is called, so override the robot
# to do that
class TestRobot(ROBOT_CLASS):
    def robotInit(self):
        try:
            super().robotInit()
        finally:
            self.__robotInitialized()


TestRobot.__name__ = ROBOT_CLASS.__name__
TestRobot.__module__ = ROBOT_CLASS.__module__
TestRobot.__qualname__ = ROBOT_CLASS.__qualname__

ROBOT_CLASS = TestRobot


if PHYSICS:
    PHYSICS.log_init_errors = False


class PyFrcNotPlugin:

    @pytest.fixture(scope="function", autouse=True)
    def robot(self):
        """
        Your robot instance

        .. note:: RobotPy/WPILib testing infrastructure is really sensitive
                  to ensuring that things get cleaned up properly. Make sure
                  that you don't store references to your robot or other
                  WPILib objects in a global or static context.
        """

        #
        # This function needs to do the same things that RobotBase.main does
        # plus some extra things needed for testing
        #
        # Previously this was separate from robot fixture, but we need to
        # ensure that the robot cleanup happens deterministically relative to
        # when handle cleanup/etc happens, otherwise unnecessary HAL errors will
        # bubble up to the user
        #

        nt_inst = ntcore.NetworkTableInstance.getDefault()
        nt_inst.startLocal()

        pauseTiming()
        restartTiming()

        wpilib.DriverStation.silenceJoystickConnectionWarning(True)
        DriverStationSim.setAutonomous(False)
        DriverStationSim.setEnabled(False)
        DriverStationSim.notifyNewData()

        robot = ROBOT_CLASS()

        # Tests only get a proxy to ensure cleanup is more reliable
        yield weakref.proxy(robot)

        # If running in separate processes, no need to do cleanup
        if ISOLATED:
            # .. and funny enough, in isolated mode we *don't* want the
            # robot to be cleaned up, as that can deadlock
            self._saved_robot = robot
            return

        # reset engine to ensure it gets cleaned up too
        # -> might be holding wpilib objects, or the robot
        if PHYSICS:
            PHYSICS.engine = None

        # HACK: avoid motor safety deadlock
        wpilib.simulation._simulation._resetMotorSafety()

        del robot

        if commands2 is not None:
            commands2.CommandScheduler.resetInstance()

        # Double-check all objects are destroyed so that HAL handles are released
        gc.collect()

        # shutdown networktables before other kinds of global cleanup
        # -> some reset functions will re-register listeners, so it's important
        #    to do this before so that the listeners are active on the current
        #    NetworkTables instance
        nt_inst.stopLocal()
        nt_inst._reset()

        # Cleanup WPILib globals
        # -> preferences, SmartDashboard, Shuffleboard, LiveWindow, MotorSafety
        wpilib.simulation._simulation._resetWpilibSimulationData()
        wpilib._wpilib._clearSmartDashboardData()
        wpilib.shuffleboard._shuffleboard._clearShuffleboardData()

        # Cancel all periodic callbacks
        hal.simulation.cancelAllSimPeriodicCallbacks()

        # Reset the HAL handles
        hal.simulation.resetGlobalHandles()

        # Reset the HAL data
        hal.simulation.resetAllSimData()

        # Don't call HAL shutdown! This is only used to cleanup HAL extensions,
        # and functions will only be called the first time (unless re-registered)
        # hal.shutdown()

    @pytest.fixture(scope="function")
    def control(self, reraise, robot: wpilib.RobotBase) -> TestController:
        """
        A pytest fixture that provides control over your robot
        """
        return TestController(reraise, robot)

    @pytest.fixture()
    def robot_file(self) -> pathlib.Path:
        """The absolute filename your robot code is started from"""
        return ROBOT_FILE

    @pytest.fixture()
    def robot_path(self) -> pathlib.Path:
        """The absolute directory that your robot code is located at"""
        return ROBOT_FILE.parent



@pytest.mark.usefixtures("control","robot_file","robot_path")
class TestThings(PyFrcNotPlugin):


    def test_iterative(self, control, robot):
        """Ensure that all states of the iterative robot run"""
        assert robot.robotInitialized == False
        assert robot.robotPeriodicCount == 0
        _test_practice(control)

        assert robot.robotInitialized == True
        assert robot.robotPeriodicCount > 0

    def test_iterative_again(self, control, robot):
        """Ensure that all states of the iterative robot run"""
        assert robot.robotInitialized == False
        assert robot.robotPeriodicCount == 0
        _test_practice(control)

        assert robot.robotInitialized == True
        assert robot.robotPeriodicCount > 0
