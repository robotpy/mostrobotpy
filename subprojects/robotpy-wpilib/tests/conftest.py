import logging

import pytest
import ntcore
import wpilib
from wpilib.simulation._simulation import _resetWpilibSimulationData

from pathlib import Path

import gc

import weakref

import hal
import hal.simulation
import wpilib.shuffleboard
from wpilib.simulation import DriverStationSim, pauseTiming, restartTiming
import wpilib.simulation
from pyfrc.test_support.controller import TestController
from pyfrc.physics.core import PhysicsInterface

try:
    import commands2
except ImportError:
    commands2 = None



@pytest.fixture
def cfg_logging(caplog):
    caplog.set_level(logging.INFO)


@pytest.fixture(scope="function")
def wpilib_state():
    try:
        yield None
    finally:
        _resetWpilibSimulationData()


@pytest.fixture(scope="function")
def nt(cfg_logging, wpilib_state):
    instance = ntcore.NetworkTableInstance.getDefault()
    instance.startLocal()

    try:
        yield instance
    finally:
        instance.stopLocal()
        instance._reset()

@pytest.fixture(scope="class", autouse=False)
def physics_and_decorated_robot_class(myrobot_class, robots_sim_enable_physics)->tuple:
    # attach physics

    robotClass = myrobot_class
    physicsInterface = None
    if robots_sim_enable_physics:
        physicsInterface, robotClass = PhysicsInterface._create_and_attach(
            myrobot_class,
            Path(__file__).parent,
        )

    if physicsInterface:
        physicsInterface.log_init_errors = False

    # Tests need to know when robotInit is called, so override the robot
    # to do that
    class TestRobot(robotClass):
        def robotInit(self):
            try:
                super().robotInit()
            finally:
                self.__robotInitialized()


    TestRobot.__name__ = robotClass.__name__
    TestRobot.__module__ = robotClass.__module__
    TestRobot.__qualname__ = robotClass.__qualname__

    return (physicsInterface, TestRobot)

@pytest.fixture(scope="function", autouse=False)
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
def getTestController(reraise, robot_with_sim_setup_teardown: wpilib.RobotBase) -> TestController:
    """
    A pytest fixture that provides control over your robot_with_sim_setup_teardown
    """
    return TestController(reraise, robot_with_sim_setup_teardown)