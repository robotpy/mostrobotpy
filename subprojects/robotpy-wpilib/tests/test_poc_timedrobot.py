"""
Proof of concept to test TimedRobotPy using PyTest

This POC was made by deconstructing pytest_plugin.py so that it is no longer a plugin but a class that provides
fixtures.

To run / debug this:

pytest subprojects/robotpy-wpilib/tests/test_poc_timedrobot.py --no-header -vvv -s

"""

import pytest
import ntcore
import wpilib
from wpilib.simulation._simulation import _resetWpilibSimulationData

import gc

import weakref

import hal
import hal.simulation
import wpilib.shuffleboard
from wpilib.simulation import pauseTiming, restartTiming
import wpilib.simulation


try:
    import commands2
except ImportError:
    commands2 = None

from wpilib.timedrobotpy import TimedRobotPy

import contextlib
import typing
import threading

from wpilib.simulation import DriverStationSim, stepTiming, stepTimingAsync


def nottest(obj):
    obj.__test__ = False
    return obj


@nottest
class TestController:
    """
    Use this object to control the robot's state during tests
    """

    def __init__(self, reraise, robot: wpilib.RobotBase):
        self._reraise = reraise

        self._thread: typing.Optional[threading.Thread] = None
        self._robot = robot

        self._cond = threading.Condition()
        self._robot_started = False
        self._robot_initialized = False
        self._robot_finished = False

    def _on_robot_initialized(self):
        with self._cond:
            self._robot_initialized = True
            self._cond.notify_all()

    def _robot_thread(self, robot):
        with self._cond:
            self._robot_started = True
            self._cond.notify_all()

        with self._reraise(catch=True):
            assert robot is not None  # shouldn't happen...

            robot._TestRobot__robotInitialized = self._on_robot_initialized

            try:
                robot.startCompetition()
                assert self._robot_finished
            finally:
                # always call endCompetition or python hangs
                robot.endCompetition()
                del robot

    @contextlib.contextmanager
    def run_robot(self):
        """
        Use this in a "with" statement to start your robot code at the
        beginning of the with block, and end your robot code at the end
        of the with block.

        Your `robotInit` function will not be called until this function
        is called.
        """

        # remove robot reference so it gets cleaned up when gc.collect() is called
        robot = self._robot
        self._robot = None

        self._thread = th = threading.Thread(
            target=self._robot_thread, args=(robot,), daemon=True
        )
        th.start()

        with self._cond:
            # make sure the thread didn't die
            assert self._cond.wait_for(lambda: self._robot_started, timeout=1)

            # If your robotInit is taking more than 2 seconds in simulation, you're
            # probably doing something wrong... but if not, please report a bug!
            assert self._cond.wait_for(lambda: self._robot_initialized, timeout=2)

        try:
            # in this block you should tell the sim to do sim things
            yield
        finally:
            self._robot_finished = True
            robot.endCompetition()

            if isinstance(self._reraise.exception, RuntimeError):
                if str(self._reraise.exception).startswith(
                    "HAL: A handle parameter was passed incorrectly"
                ):
                    msg = (
                        "Do not reuse HAL objects in tests! This error may occur if you"
                        " stored a motor/sensor as a global or as a class variable"
                        " outside of a method."
                    )
                    if hasattr(Exception, "add_note"):
                        self._reraise.exception.add_note(f"*** {msg}")
                    else:
                        e = self._reraise.exception
                        self._reraise.reset()
                        raise RuntimeError(msg) from e

        # Increment time by 1 second to ensure that any notifiers fire
        stepTimingAsync(1.0)

        # the robot thread should exit quickly
        th.join(timeout=1)
        if th.is_alive():
            pytest.fail("robot did not exit within 2 seconds")

        self._robot = None
        self._thread = None

    @property
    def robot_is_alive(self) -> bool:
        """
        True if the robot code is alive
        """
        th = self._thread
        if not th:
            return False

        return th.is_alive()

    def step_timing(
        self,
        *,
        seconds: float,
        autonomous: bool,
        enabled: bool,
        assert_alive: bool = True,
    ) -> float:
        """
        This utility will increment simulated time, while pretending that
        there's a driver station connected and delivering new packets
        every 0.2 seconds.

        :param seconds:    Number of seconds to run (will step in increments of 0.2)
        :param autonomous: Tell the robot that it is in autonomous mode
        :param enabled:    Tell the robot that it is enabled

        :returns: Number of seconds time was incremented
        """

        assert self.robot_is_alive, "did you call control.run_robot()?"

        assert seconds > 0

        DriverStationSim.setDsAttached(True)
        DriverStationSim.setAutonomous(autonomous)
        DriverStationSim.setEnabled(enabled)

        tm = 0.0

        while tm < seconds + 0.01:
            DriverStationSim.notifyNewData()
            stepTiming(0.2)
            if assert_alive:
                assert self.robot_is_alive
            tm += 0.2

        return tm


@pytest.fixture(scope="function")
def decorated_robot_class(myrobot_class) -> tuple:
    # attach physics

    robotClass = myrobot_class

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

    return TestRobot


@pytest.fixture(scope="function", autouse=False)
def robot_with_sim_setup_teardown(decorated_robot_class):
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

    robot = decorated_robot_class()

    # Tests only get a proxy to ensure cleanup is more reliable
    yield weakref.proxy(robot)

    # If running in separate processes, no need to do cleanup
    # if ISOLATED:
    #    # .. and funny enough, in isolated mode we *don't* want the
    #    # robot to be cleaned up, as that can deadlock
    #    self._saved_robot = robot
    #    return

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
def getTestController(
    reraise, robot_with_sim_setup_teardown: wpilib.RobotBase
) -> TestController:
    """
    A pytest fixture that provides control over your robot_with_sim_setup_teardown
    """
    return TestController(reraise, robot_with_sim_setup_teardown)


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


class TestThings:

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

    @classmethod
    @pytest.fixture(scope="function", autouse=True)
    def myrobot_class(cls) -> type[MyRobot]:
        return cls.MyRobot

    def test_iterative(self, getTestController, robot_with_sim_setup_teardown):
        """Ensure that all states of the iterative robot run"""
        assert robot_with_sim_setup_teardown.robotInitialized == False
        assert robot_with_sim_setup_teardown.robotPeriodicCount == 0
        run_practice(getTestController)

        assert robot_with_sim_setup_teardown.robotInitialized == True
        assert robot_with_sim_setup_teardown.robotPeriodicCount > 0

    def test_iterative_again(self, getTestController, robot_with_sim_setup_teardown):
        """Ensure that all states of the iterative robot run"""
        assert robot_with_sim_setup_teardown.robotInitialized == False
        assert robot_with_sim_setup_teardown.robotPeriodicCount == 0
        run_practice(getTestController)

        assert robot_with_sim_setup_teardown.robotInitialized == True
        assert robot_with_sim_setup_teardown.robotPeriodicCount > 0

class MyRobotRobotInitFails(TimedRobotPy):
    def robotInit(self):
        assert False

class MyRobotRobotPeriodicFails(TimedRobotPy):
    def robotPeriodic(self):
        assert False

class MyRobotAutonomousInitFails(TimedRobotPy):
    def autonomousInit(self):
        assert False

class MyRobotAutonomousPeriodicFails(TimedRobotPy):
    def autonomousPeriodic(self):
        assert False

class MyRobotAutonomousExitFails(TimedRobotPy):
    def autonomousExit(self):
        assert False

class MyRobotTeleopInitFails(TimedRobotPy):
    def teleopInit(self):
        assert False

class MyRobotTeleopPeriodicFails(TimedRobotPy):
    def teleopPeriodic(self):
        assert False

class MyRobotDisabledPeriodicFails(TimedRobotPy):
    def disabledPeriodic(self):
        assert False

class MyRobotDisabledInitFails(TimedRobotPy):
    def disabledInit(self):
        assert False

class MyRobotTestInitFails(TimedRobotPy):
    def testInit(self):
        assert False

class MyRobotTestPeriodicFails(TimedRobotPy):
    def testPeriodic(self):
        assert False

"""
@pytest.mark.parametrize("myrobot_class", [
    MyRobotRobotInitFails,
    MyRobotAutonomousInitFails,
    MyRobotAutonomousPeriodicFails,
    MyRobotAutonomousExitFails,
])
class TestCanThrowFailures:


    def test_autonomous_fails(self, getTestController, robot_with_sim_setup_teardown):
        with getTestController.run_robot():
            hasAssertionError = False
            try:
                # Run disabled for a short period
                getTestController.step_timing(seconds=0.5, autonomous=True, enabled=False)

                # Run autonomous + enabled for 15 seconds
                getTestController.step_timing(seconds=15, autonomous=True, enabled=True)

                # Disabled for another short period
                getTestController.step_timing(seconds=0.5, autonomous=False, enabled=False)
            except AssertionError:
                hasAssertionError = True
                print("We had an assertion error")
            assert hasAssertionError
"""


