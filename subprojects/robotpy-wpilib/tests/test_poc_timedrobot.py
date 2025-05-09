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


import gc

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


@pytest.fixture(scope="module", autouse=True)
def myrobot_class()->type[MyRobot]:
    return MyRobot


@pytest.fixture(scope="module", autouse=True)
def physics_and_decorated_robot_class(myrobot_class)->tuple:
    # attach physics
    PHYSICS, ROBOT_CLASS = PhysicsInterface._create_and_attach(
        myrobot_class,
        Path(__file__).parent,
    )

    if PHYSICS:
        PHYSICS.log_init_errors = False

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

    return (PHYSICS, TestRobot)





@pytest.fixture(scope="function", autouse=True)
def robot_with_sim_setup_teardown(physics_and_decorated_robot_class):
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

    robot = physics_and_decorated_robot_class[1]()

    # Tests only get a proxy to ensure cleanup is more reliable
    yield weakref.proxy(robot)

    # If running in separate processes, no need to do cleanup
    #if ISOLATED:
    #    # .. and funny enough, in isolated mode we *don't* want the
    #    # robot to be cleaned up, as that can deadlock
    #    self._saved_robot = robot
    #    return

    # reset engine to ensure it gets cleaned up too
    # -> might be holding wpilib objects, or the robot
    if physics_and_decorated_robot_class[0]:
        physics_and_decorated_robot_class[0].engine = None

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
def control(reraise, robot_with_sim_setup_teardown: wpilib.RobotBase) -> TestController:
    """
    A pytest fixture that provides control over your robot_with_sim_setup_teardown
    """
    return TestController(reraise, robot_with_sim_setup_teardown)

#@pytest.fixture()
#def robot_file() -> pathlib.Path:
#    """The absolute filename your robot code is started from"""
#    return ROBOT_FILE

#@pytest.fixture()
#def robot_path() -> pathlib.Path:
#    """The absolute directory that your robot code is located at"""
#    return ROBOT_FILE.parent


def run_practice(control: "TestController"):
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
class TestThings():


    def test_iterative(self, control, robot_with_sim_setup_teardown):
        """Ensure that all states of the iterative robot run"""
        assert robot_with_sim_setup_teardown.robotInitialized == False
        assert robot_with_sim_setup_teardown.robotPeriodicCount == 0
        run_practice(control)

        assert robot_with_sim_setup_teardown.robotInitialized == True
        assert robot_with_sim_setup_teardown.robotPeriodicCount > 0

    def test_iterative_again(self, control, robot_with_sim_setup_teardown):
        """Ensure that all states of the iterative robot run"""
        assert robot_with_sim_setup_teardown.robotInitialized == False
        assert robot_with_sim_setup_teardown.robotPeriodicCount == 0
        run_practice(control)

        assert robot_with_sim_setup_teardown.robotInitialized == True
        assert robot_with_sim_setup_teardown.robotPeriodicCount > 0
