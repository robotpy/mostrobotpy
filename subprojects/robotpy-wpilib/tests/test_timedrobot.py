""" "

Test TimedRobotPy and IterativeRobotPy

To run / debug this:

pytest subprojects/robotpy-wpilib/tests/test_timedrobot.py --no-header -vvv -s

"""

import contextlib
from enum import Enum
import gc
import pytest
import threading
import traceback
import typing
import weakref

import ntcore
import hal
import hal.simulation
import wpilib
from wpilib import RobotController
import wpilib.shuffleboard
from wpilib.simulation._simulation import _resetWpilibSimulationData
import wpilib.simulation
from wpilib.simulation import pauseTiming, restartTiming
from wpilib.simulation import DriverStationSim, stepTiming, stepTimingAsync
from wpilib.timedrobotpy import TimedRobotPy, _Callback
from wpilib import TimedRobot


def test_calcFutureExpirationUs() -> None:
    cb = _Callback(func=None, periodUs=20_000, expirationUs=100)
    assert cb.calcFutureExpirationUs(100) == 20_100
    assert cb.calcFutureExpirationUs(101) == 20_100
    assert cb.calcFutureExpirationUs(20_099) == 20_100
    assert cb.calcFutureExpirationUs(20_100) == 40_100
    assert cb.calcFutureExpirationUs(20_101) == 40_100

    cb = _Callback(func=None, periodUs=40_000, expirationUs=500)
    assert cb.calcFutureExpirationUs(500) == 40_500
    assert cb.calcFutureExpirationUs(501) == 40_500
    assert cb.calcFutureExpirationUs(40_499) == 40_500
    assert cb.calcFutureExpirationUs(40_500) == 80_500
    assert cb.calcFutureExpirationUs(40_501) == 80_500

    cb = _Callback(func=None, periodUs=1_000, expirationUs=0)
    assert (
        cb.calcFutureExpirationUs(1_000_000_000_000_000_000)
        == 1_000_000_000_000_001_000
    )
    assert (
        cb.calcFutureExpirationUs(1_000_000_000_000_000_001)
        == 1_000_000_000_000_001_000
    )
    assert (
        cb.calcFutureExpirationUs(1_000_000_000_000_000_999)
        == 1_000_000_000_000_001_000
    )
    assert (
        cb.calcFutureExpirationUs(1_000_000_000_000_001_000)
        == 1_000_000_000_000_002_000
    )
    assert (
        cb.calcFutureExpirationUs(1_000_000_000_000_001_001)
        == 1_000_000_000_000_002_000
    )


def nottest(obj):
    obj.__test__ = False
    return obj


@nottest
class TestController:
    """
    Use this object to control the robot's state during tests
    """

    def __init__(self, reraise, robot: wpilib.RobotBase, expectFinished: bool) -> None:
        self._reraise = reraise

        self._thread: typing.Optional[threading.Thread] = None
        self._robot = robot
        self._expectFinished = expectFinished

        self._cond = threading.Condition()
        self._robotStarted = False
        self._robotInitStarted = False
        self._robotFinished = False
        self._startCompetitionReturned = False

    def _onRobotInitStarted(self) -> None:
        with self._cond:
            self._robotInitStarted = True
            self._cond.notify_all()

    def _robotThread(self, robot: TimedRobotPy) -> None:
        with self._cond:
            self._robotStarted = True
            self._cond.notify_all()

        with self._reraise(catch=False):
            assert robot is not None  # shouldn't happen...

            robot._TestRobot__robotInitStarted = self._onRobotInitStarted

            try:
                robot.startCompetition()
                self._startCompetitionReturned = True

            except Exception as e:
                # Print the exception type and message
                print(f"_robotThread: Exception caught: {type(e).__name__}: {e}")

                if self._expectFinished:
                    # Print the stack trace
                    print("Stack trace:")
                    traceback.print_exc()

                # Rethrow the exception to propagate it up the call stack
                raise

            finally:
                del robot

    @contextlib.contextmanager
    def runRobot(self) -> None:
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
            target=self._robotThread, args=(robot,), daemon=True
        )
        th.start()

        with self._cond:
            # make sure the thread didn't die
            assert self._cond.wait_for(lambda: self._robotStarted, timeout=1)

            # If your robotInit is taking more than 2 seconds in simulation, you're
            # probably doing something wrong... but if not, please report a bug!
            assert self._cond.wait_for(lambda: self._robotInitStarted, timeout=2)

        try:
            # in this block you should tell the sim to do sim things
            yield
        except Exception as e:
            # Print the exception type and message
            print(f"runRobot: Exception caught: {type(e).__name__}: {e}")

            if self._expectFinished:
                # Print the stack trace
                print("Stack trace:")
                traceback.print_exc()

            # Rethrow the exception to propagate it up the call stack
            raise
        finally:
            self._robotFinished = True
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

        if not self._expectFinished:
            assert type(self._reraise.reset()) is AssertionError

        self._thread = None

        assert self._expectFinished == self._startCompetitionReturned

    @property
    def robotIsAlive(self) -> bool:
        """
        True if the robot code is alive
        """
        th = self._thread
        if not th:
            return False

        return th.is_alive()

    def stepTiming(
        self,
        *,
        seconds: float,
        autonomous: bool = False,
        test: bool = False,
        enabled: bool = False,
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

        if self._expectFinished:
            assert self.robotIsAlive, "did you call control.run_robot()?"

        assert seconds > 0

        DriverStationSim.setDsAttached(True)
        DriverStationSim.setAutonomous(autonomous)
        DriverStationSim.setTest(test)
        DriverStationSim.setEnabled(enabled)

        tm = 0.0

        while tm < seconds:
            DriverStationSim.notifyNewData()
            stepTiming(0.001)
            if assert_alive and self._expectFinished:
                if not self.robotIsAlive:
                    print("not self.robotIsAlive", flush=True)
                assert self.robotIsAlive
            tm += 0.001

        return tm


@pytest.fixture(scope="function")
def decorated_robot_class(myrobot_class) -> tuple:
    # attach physics

    robotClass = myrobot_class

    # Tests need to know when robotInit is called, so override the robot
    # to do that
    class TestRobot(robotClass):
        def robotInit(self):
            self.__robotInitStarted()
            super().robotInit()

    TestRobot.__name__ = robotClass.__name__
    TestRobot.__module__ = robotClass.__module__
    TestRobot.__qualname__ = robotClass.__qualname__

    return TestRobot


@pytest.fixture(scope="function")
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

    # HACK: avoid motor safety deadlock
    wpilib.simulation._simulation._resetMotorSafety()

    del robot

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
def get_test_controller(
    reraise, robot_with_sim_setup_teardown: wpilib.RobotBase, expect_finished: bool
) -> TestController:
    """
    A pytest fixture that provides control over your robot_with_sim_setup_teardown
    """
    return TestController(reraise, robot_with_sim_setup_teardown, expect_finished)


class TimedRobotPyExpectsException(TimedRobotPy):

    def __init__(self, period=TimedRobotPy.kDefaultPeriod):
        super().__init__(period=period)
        self._callOrder = ":"

    def startCompetition(self) -> None:
        hasAssertionError = False
        try:
            super().startCompetition()
        except AssertionError as e:
            hasAssertionError = True

            # Print the exception type and message
            print(
                f"TimedRobotPyExpectsException AssertionError: Exception caught: {type(e).__name__}: {e}"
            )

            if False:
                # Print the stack trace
                print("Stack trace:")
                traceback.print_exc()

            # Rethrow the exception to propagate it up the call stack
            raise

        except Exception as e:
            # Print the exception type and message
            print(
                f"TimedRobotPyExpectsException Exception caught: {type(e).__name__}: {e}"
            )

            # Print the stack trace
            print("Stack trace:")
            traceback.print_exc()

            # Rethrow the exception to propagate it up the call stack
            raise

        finally:
            print(f"TimedRobotPyExpectsException hasAssertionError={hasAssertionError}")
            assert hasAssertionError


class TimedRobotPyDoNotExpectException(TimedRobotPy):

    def __init__(self, period=TimedRobotPy.kDefaultPeriod):
        super().__init__(period=period)
        self._callOrder = ":"

    def startCompetition(self) -> None:
        hasAssertionError = False
        try:
            super().startCompetition()
        except AssertionError:
            hasAssertionError = True
            # Print the exception type and message
            print(f"Exception caught: {type(e).__name__}: {e}")

            # Print the stack trace
            print("Stack trace:")
            traceback.print_exc()

            # Rethrow the exception to propagate it up the call stack
            raise
        except Exception as e:
            # Print the exception type and message
            print(f"Exception caught: {type(e).__name__}: {e}")

            # Print the stack trace
            print("Stack trace:")
            traceback.print_exc()

            # Rethrow the exception to propagate it up the call stack
            raise

        finally:
            print(f"TimedRobotPyExpectsException hasAssertionError={hasAssertionError}")
            assert not hasAssertionError


def getFPGATimeInSecondsAsStr():
    return f"{RobotController.getFPGATime()/1000_000.0:.3f}s"


def printEntryAndExit(func):
    def wrapper(*args, **kwargs):
        name = func.__name__
        args[0]._callOrder += name + "+:"
        print(f"{getFPGATimeInSecondsAsStr()}:Enter:{name}")
        result = func(*args, **kwargs)
        args[0]._callOrder += name + "-:"
        print(f"{getFPGATimeInSecondsAsStr()}:Exit_:{name}")
        return result

    return wrapper


class MyRobotDefaultPass:

    @printEntryAndExit
    def robotInit(self):
        pass

    @printEntryAndExit
    def robotPeriodic(self):
        pass

    @printEntryAndExit
    def autonomousInit(self):
        pass

    @printEntryAndExit
    def autonomousPeriodic(self):
        pass

    @printEntryAndExit
    def autonomousExit(self):
        pass

    @printEntryAndExit
    def teleopInit(self):
        pass

    @printEntryAndExit
    def teleopPeriodic(self):
        pass

    @printEntryAndExit
    def teleopExit(self):
        pass

    @printEntryAndExit
    def testInit(self):
        pass

    @printEntryAndExit
    def testPeriodic(self):
        pass

    @printEntryAndExit
    def testExit(self):
        pass

    @printEntryAndExit
    def disabledInit(self):
        pass

    @printEntryAndExit
    def disabledPeriodic(self):
        pass

    @printEntryAndExit
    def disabledExit(self):
        pass

    @printEntryAndExit
    def _simulationInit(self):
        pass

    @printEntryAndExit
    def _simulationPeriodic(self):
        pass


class MyRobotRobotInitFails(MyRobotDefaultPass):
    @printEntryAndExit
    def robotInit(self):
        assert False


class MyRobotRobotPeriodicFails(MyRobotDefaultPass):
    @printEntryAndExit
    def robotPeriodic(self):
        assert False


class MyRobotAutonomousInitFails(MyRobotDefaultPass):
    @printEntryAndExit
    def autonomousInit(self):
        assert False


class MyRobotAutonomousPeriodicFails(MyRobotDefaultPass):
    @printEntryAndExit
    def autonomousPeriodic(self):
        assert False


class MyRobotAutonomousExitFails(MyRobotDefaultPass):
    @printEntryAndExit
    def autonomousExit(self):
        assert False


class MyRobotTeleopInitFails(MyRobotDefaultPass):
    @printEntryAndExit
    def teleopInit(self):
        assert False


class MyRobotTeleopPeriodicFails(MyRobotDefaultPass):
    @printEntryAndExit
    def teleopPeriodic(self):
        assert False


class MyRobotTeleopExitFails(MyRobotDefaultPass):
    @printEntryAndExit
    def teleopExit(self):
        assert False


class MyRobotDisabledInitFails(MyRobotDefaultPass):
    @printEntryAndExit
    def disabledInit(self):
        assert False


class MyRobotDisabledPeriodicFails(MyRobotDefaultPass):
    @printEntryAndExit
    def disabledPeriodic(self):
        assert False


class MyRobotDisabledExitFails(MyRobotDefaultPass):
    @printEntryAndExit
    def disabledExit(self):
        assert False


class MyRobotTestInitFails(MyRobotDefaultPass):
    @printEntryAndExit
    def testInit(self):
        assert False


class MyRobotTestPeriodicFails(MyRobotDefaultPass):
    @printEntryAndExit
    def testPeriodic(self):
        assert False


class MyRobotTestExitFails(MyRobotDefaultPass):
    @printEntryAndExit
    def testExit(self):
        assert False


class MyRobotSimulationInitFails(MyRobotDefaultPass):
    @printEntryAndExit
    def _simulationInit(self):
        assert False


class MyRobotSimulationPeriodicFails(MyRobotDefaultPass):
    @printEntryAndExit
    def _simulationPeriodic(self):
        assert False


class ExpectFinished(Enum):
    kNotFinished = 0
    kFinished = 1


class RobotMode(Enum):
    kNone = 0
    kDisabled = 1
    kAutonomous = 2
    kTeleop = 3
    kTest = 4

    def __init__(self, code):
        self._code = code

    @property
    def autonomous(self):
        return self is RobotMode.kAutonomous

    @property
    def test(self):
        return self is RobotMode.kTest

    @property
    def enabled(self):
        return (self is not RobotMode.kDisabled) and (self is not RobotMode.kNone)


from dataclasses import dataclass, field


@dataclass()
class CaseConfiguration:
    """Class for configuration of Test Cases"""

    description: str
    myRobotAddMethods: type
    timedRobotExpectation: TimedRobotPy
    robotMode: RobotMode = None
    expectFinished: ExpectFinished = ExpectFinished.kFinished
    callSequenceStr: str = None


@pytest.fixture(scope="function")
def myrobot_class(
    caseConfiguration,
) -> type[TimedRobotPy]:

    print(f"\ndescription=\n\n{caseConfiguration.description}\n")
    print(f"myRobotAddMethods={caseConfiguration.myRobotAddMethods.__name__}")
    print(f"timedRobotExpectation={caseConfiguration.timedRobotExpectation.__name__}")
    print(f"robotMode={caseConfiguration.robotMode}")
    print(f"expectFinished={caseConfiguration.expectFinished}")
    print(f"callSequenceStr={caseConfiguration.callSequenceStr}\n\n")

    class MyRobot(
        caseConfiguration.myRobotAddMethods, caseConfiguration.timedRobotExpectation
    ):

        @printEntryAndExit
        def startCompetition(self):
            super().startCompetition()

        @printEntryAndExit
        def endCompetition(self):
            super().endCompetition()

    return MyRobot


@pytest.fixture(scope="function")
def expect_finished(caseConfiguration) -> bool:
    return caseConfiguration.expectFinished is ExpectFinished.kFinished


@pytest.fixture(scope="function")
def robot_mode_fixture(caseConfiguration) -> RobotMode:
    return caseConfiguration.robotMode


@pytest.fixture(scope="function")
def call_sequence_str(caseConfiguration) -> str:
    return caseConfiguration.callSequenceStr


@pytest.mark.filterwarnings("ignore:Exception in thread")
@pytest.mark.parametrize(
    "caseConfiguration",
    [
        CaseConfiguration(
            description="Robot enters autonomous mode without exceptions",
            myRobotAddMethods=MyRobotDefaultPass,
            timedRobotExpectation=TimedRobotPyDoNotExpectException,
            expectFinished=ExpectFinished.kFinished,
            robotMode=RobotMode.kAutonomous,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":autonomousInit+:autonomousInit-:autonomousPeriodic+:autonomousPeriodic-"
            ":robotPeriodic+:robotPeriodic-:_simulationPeriodic+:_simulationPeriodic-"
            ":autonomousExit+:autonomousExit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:",
        ),
        CaseConfiguration(
            description="Robot enters teleop mode without exceptions",
            myRobotAddMethods=MyRobotDefaultPass,
            timedRobotExpectation=TimedRobotPyDoNotExpectException,
            expectFinished=ExpectFinished.kFinished,
            robotMode=RobotMode.kTeleop,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":teleopInit+:teleopInit-:teleopPeriodic+:teleopPeriodic-"
            ":robotPeriodic+:robotPeriodic-:_simulationPeriodic+:_simulationPeriodic-"
            ":teleopExit+:teleopExit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:",
        ),
        CaseConfiguration(
            description="Robot enters test mode without exceptions",
            myRobotAddMethods=MyRobotDefaultPass,
            timedRobotExpectation=TimedRobotPyDoNotExpectException,
            expectFinished=ExpectFinished.kFinished,
            robotMode=RobotMode.kTest,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":testInit+:testInit-:testPeriodic+:testPeriodic-"
            ":robotPeriodic+:robotPeriodic-:_simulationPeriodic+:_simulationPeriodic-"
            ":testExit+:testExit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:",
        ),
        CaseConfiguration(
            description="Robot enters autonomous mode, exception in robotInit",
            myRobotAddMethods=MyRobotRobotInitFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kAutonomous,
            callSequenceStr=":startCompetition+:robotInit+:",
        ),
        CaseConfiguration(
            description="Robot enters autonomous mode, exception in simulationInit",
            myRobotAddMethods=MyRobotSimulationInitFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kAutonomous,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:",
        ),
        CaseConfiguration(
            description="Robot enters autonomous mode, exception in robotPeriodic",
            myRobotAddMethods=MyRobotRobotPeriodicFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kAutonomous,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:",
        ),
        CaseConfiguration(
            description="Robot enters autonomous mode, exception in simulationPeriodic",
            myRobotAddMethods=MyRobotSimulationPeriodicFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kAutonomous,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:",
        ),
        CaseConfiguration(
            description="Robot enters autonomous mode, exception in disabledInit",
            myRobotAddMethods=MyRobotDisabledInitFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kAutonomous,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:",
        ),
        CaseConfiguration(
            description="Robot enters autonomous mode, exception in disabledPeriodic",
            myRobotAddMethods=MyRobotDisabledPeriodicFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kAutonomous,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:",
        ),
        CaseConfiguration(
            description="Robot enters autonomous mode, exception in disabledExit",
            myRobotAddMethods=MyRobotDisabledExitFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kAutonomous,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:",
        ),
        CaseConfiguration(
            description="Robot enters autonomous mode, exception in autonomousInit",
            myRobotAddMethods=MyRobotAutonomousInitFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kAutonomous,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":autonomousInit+:",
        ),
        CaseConfiguration(
            description="Robot enters autonomous mode, exception in autonomousPeriodic",
            myRobotAddMethods=MyRobotAutonomousPeriodicFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kAutonomous,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":autonomousInit+:autonomousInit-:autonomousPeriodic+:",
        ),
        CaseConfiguration(
            description="Robot enters autonomous mode, exception in autonomousExit",
            myRobotAddMethods=MyRobotAutonomousExitFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kAutonomous,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":autonomousInit+:autonomousInit-:autonomousPeriodic+:autonomousPeriodic-"
            ":robotPeriodic+:robotPeriodic-:_simulationPeriodic+:_simulationPeriodic-"
            ":autonomousExit+:",
        ),
        CaseConfiguration(
            description="Robot enters teleop mode, exception in teleopInit",
            myRobotAddMethods=MyRobotTeleopInitFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kTeleop,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":teleopInit+:",
        ),
        CaseConfiguration(
            description="Robot enters teleop mode, exception in teleopPeriodic",
            myRobotAddMethods=MyRobotTeleopPeriodicFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kTeleop,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":teleopInit+:teleopInit-:teleopPeriodic+:",
        ),
        CaseConfiguration(
            description="Robot enters teleop mode, exception in teleopExit",
            myRobotAddMethods=MyRobotTeleopExitFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kTeleop,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":teleopInit+:teleopInit-:teleopPeriodic+:teleopPeriodic-"
            ":robotPeriodic+:robotPeriodic-:_simulationPeriodic+:_simulationPeriodic-"
            ":teleopExit+:",
        ),
        CaseConfiguration(
            description="Robot enters test mode, exception in testInit",
            myRobotAddMethods=MyRobotTestInitFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kTest,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":testInit+:",
        ),
        CaseConfiguration(
            description="Robot enters test mode, exception in testPeriodic",
            myRobotAddMethods=MyRobotTestPeriodicFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kTest,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":testInit+:testInit-:testPeriodic+:",
        ),
        CaseConfiguration(
            description="Robot enters test mode, exception in testExit",
            myRobotAddMethods=MyRobotTestExitFails,
            timedRobotExpectation=TimedRobotPyExpectsException,
            expectFinished=ExpectFinished.kNotFinished,
            robotMode=RobotMode.kTest,
            callSequenceStr=":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":testInit+:testInit-:testPeriodic+:testPeriodic-"
            ":robotPeriodic+:robotPeriodic-:_simulationPeriodic+:_simulationPeriodic-"
            ":testExit+:",
        ),
    ],
)
class TestCanThrowExceptions:

    def test_robot_mode_with_exceptions(
        self,
        get_test_controller,
        robot_with_sim_setup_teardown,
        robot_mode_fixture,
        call_sequence_str,
    ):
        with get_test_controller.runRobot():
            rmf = robot_mode_fixture
            periodS = robot_with_sim_setup_teardown.getPeriod()
            # Run disabled for a short period
            print(
                f"periodS={periodS} or {periodS*1.5} a={rmf.autonomous} t={rmf.test} e={rmf.enabled}"
            )
            get_test_controller.stepTiming(
                seconds=periodS * 1.5,
                autonomous=rmf.autonomous,
                test=rmf.test,
                enabled=False,
            )

            # Run in desired mode for 1 period
            get_test_controller.stepTiming(
                seconds=periodS,
                autonomous=rmf.autonomous,
                test=rmf.test,
                enabled=rmf.enabled,
            )

            # Disabled for 1 period
            get_test_controller.stepTiming(
                seconds=periodS, autonomous=rmf.autonomous, test=rmf.test, enabled=False
            )
            print(f"result={robot_with_sim_setup_teardown._callOrder}")
            assert robot_with_sim_setup_teardown._callOrder == call_sequence_str


@pytest.mark.parametrize(
    "caseConfiguration",
    [
        CaseConfiguration(
            description="Robot enters autonomous, disabled, teleop, and test modes.",
            myRobotAddMethods=MyRobotDefaultPass,
            timedRobotExpectation=TimedRobotPyDoNotExpectException,
            expectFinished=ExpectFinished.kFinished,
        ),
    ],
)
class TestSequenceThroughModes:

    def test_robot_mode_sequence(
        self,
        get_test_controller,
        robot_with_sim_setup_teardown,
    ):
        callSequenceStr = (
            ":startCompetition+:robotInit+:robotInit-:_simulationInit+:_simulationInit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":autonomousInit+:autonomousInit-"
            ":autonomousPeriodic+:autonomousPeriodic-"
            ":robotPeriodic+:robotPeriodic-:_simulationPeriodic+:_simulationPeriodic-"
            ":autonomousPeriodic+:autonomousPeriodic-"
            ":robotPeriodic+:robotPeriodic-:_simulationPeriodic+:_simulationPeriodic-"
            ":autonomousExit+:autonomousExit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":teleopInit+:teleopInit-"
            ":teleopPeriodic+:teleopPeriodic-"
            ":robotPeriodic+:robotPeriodic-:_simulationPeriodic+:_simulationPeriodic-"
            ":teleopPeriodic+:teleopPeriodic-"
            ":robotPeriodic+:robotPeriodic-:_simulationPeriodic+:_simulationPeriodic-"
            ":teleopExit+:teleopExit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:disabledExit+:disabledExit-"
            ":testInit+:testInit-"
            ":testPeriodic+:testPeriodic-"
            ":robotPeriodic+:robotPeriodic-:_simulationPeriodic+:_simulationPeriodic-"
            ":testPeriodic+:testPeriodic-"
            ":robotPeriodic+:robotPeriodic-:_simulationPeriodic+:_simulationPeriodic-"
            ":testExit+:testExit-"
            ":disabledInit+:disabledInit-:disabledPeriodic+:disabledPeriodic-:robotPeriodic+:robotPeriodic-"
            ":_simulationPeriodic+:_simulationPeriodic-:"
        )

        with get_test_controller.runRobot():
            periodS = robot_with_sim_setup_teardown.getPeriod()
            # Run disabled for a short period
            get_test_controller.stepTiming(
                seconds=periodS * 1.5,
                autonomous=True,
                test=False,
                enabled=False,
            )

            # Run in autonomous mode for 2 periods
            get_test_controller.stepTiming(
                seconds=periodS * 2,
                autonomous=True,
                test=False,
                enabled=True,
            )

            # Disabled for 1 period
            get_test_controller.stepTiming(
                seconds=periodS, autonomous=False, test=False, enabled=False
            )

            # Run in teleop mode for 2 periods
            get_test_controller.stepTiming(
                seconds=periodS * 2,
                autonomous=False,
                test=False,
                enabled=True,
            )

            # Disabled for 1 period
            get_test_controller.stepTiming(
                seconds=periodS, autonomous=False, test=False, enabled=False
            )

            # Run in test mode for 2 periods
            get_test_controller.stepTiming(
                seconds=periodS * 2,
                autonomous=False,
                test=True,
                enabled=True,
            )

            # Disabled for 1 period
            get_test_controller.stepTiming(
                seconds=periodS, autonomous=False, test=False, enabled=False
            )

            print(f"result={robot_with_sim_setup_teardown._callOrder}")
            assert robot_with_sim_setup_teardown._callOrder == callSequenceStr


class TimedRobotDoNotExpectException(TimedRobot):

    def __init__(self, period=TimedRobotPy.kDefaultPeriod):
        super().__init__(period=period)
        self._callOrder = ":"

    def startCompetition(self) -> None:
        hasAssertionError = False
        try:
            super().startCompetition()
        except AssertionError:
            hasAssertionError = True
        print(f"TimedRobotPyExpectsException hasAssertionError={hasAssertionError}")
        assert not hasAssertionError


class TimedRobotDoNotExpectException1msPeriod(TimedRobotDoNotExpectException):

    def __init__(self, period=0.010):
        super().__init__(period=period)


class TimedRobotPyDoNotExpectException1msPeriod(TimedRobotPyDoNotExpectException):

    def __init__(self, period=0.010):
        super().__init__(period=period)


class MyRobotAddPeriodic:

    def addCallLog(self, name: str):
        self._calls.append({"name": name, "time": RobotController.getFPGATime()})
        if name not in self._callCount:
            self._callCount[name] = 0
        self._callCount[name] += 1

    @printEntryAndExit
    def _periodicN(self, name: str):
        print(
            f"{getFPGATimeInSecondsAsStr()}:Function {name} executed count={self.count}"
        )
        self.addCallLog(name)

    @printEntryAndExit
    def robotInit(self):
        self.count = 0

        self._calls = []
        self._callCount = {}

        self.addPeriodic(lambda: self._periodicN("periodic_0_0"), 0.010, 0.001)
        self.addPeriodic(lambda: self._periodicN("periodic_0_1"), 0.010, 0.001)

    @printEntryAndExit
    def robotPeriodic(self):
        self.count += 1
        self.addCallLog("robotPeriodic")

        name = f"periodic_{self.count}"

        def periodic_N():
            self._periodicN(name)

        self.addPeriodic(periodic_N, 0.020, 0.002)


@pytest.mark.parametrize(
    "caseConfiguration",
    [
        CaseConfiguration(
            description="Robot uses addPeriodic to add periodic functions",
            myRobotAddMethods=MyRobotAddPeriodic,
            timedRobotExpectation=TimedRobotDoNotExpectException1msPeriod,
            expectFinished=ExpectFinished.kFinished,
        ),
    ],
)
class TestSequenceAddPeriodics:

    def test_robot_add_periodic(
        self,
        get_test_controller,
        robot_with_sim_setup_teardown,
    ):

        with get_test_controller.runRobot():
            periodS = robot_with_sim_setup_teardown.getPeriod()
            # Run disabled for a short period
            get_test_controller.stepTiming(
                seconds=periodS * 1.5,
                autonomous=True,
                test=False,
                enabled=False,
            )

            for key, value in robot_with_sim_setup_teardown._callCount.items():
                print(f"{key}:callCount={value}")

            assert robot_with_sim_setup_teardown._callCount["robotPeriodic"] == 1
            assert robot_with_sim_setup_teardown._callCount["periodic_0_0"] == 1
            assert robot_with_sim_setup_teardown._callCount["periodic_0_1"] == 1

            # Run disabled mode for 1 period
            get_test_controller.stepTiming(
                seconds=periodS,
                autonomous=False,
                test=False,
                enabled=False,
            )

            for key, value in robot_with_sim_setup_teardown._callCount.items():
                print(f"{key}:callCount={value}")

            assert robot_with_sim_setup_teardown._callCount["robotPeriodic"] == 2
            assert robot_with_sim_setup_teardown._callCount["periodic_0_0"] == 2
            assert robot_with_sim_setup_teardown._callCount["periodic_0_1"] == 2
            assert robot_with_sim_setup_teardown._callCount["periodic_1"] == 1

            # Run disabled mode for 1 period
            get_test_controller.stepTiming(
                seconds=periodS,
                autonomous=False,
                test=False,
                enabled=False,
            )

            for key, value in robot_with_sim_setup_teardown._callCount.items():
                print(f"{key}:callCount={value}")

            assert robot_with_sim_setup_teardown._callCount["robotPeriodic"] == 3
            assert robot_with_sim_setup_teardown._callCount["periodic_0_0"] == 3
            assert robot_with_sim_setup_teardown._callCount["periodic_0_1"] == 3
            assert robot_with_sim_setup_teardown._callCount["periodic_1"] == 1

            # Run disabled mode for 1 period
            get_test_controller.stepTiming(
                seconds=periodS,
                autonomous=False,
                test=False,
                enabled=False,
            )

            for key, value in robot_with_sim_setup_teardown._callCount.items():
                print(f"{key}:callCount={value}")

            assert robot_with_sim_setup_teardown._callCount["robotPeriodic"] == 4
            assert robot_with_sim_setup_teardown._callCount["periodic_0_0"] == 4
            assert robot_with_sim_setup_teardown._callCount["periodic_0_1"] == 4
            assert robot_with_sim_setup_teardown._callCount["periodic_1"] == 2
            assert robot_with_sim_setup_teardown._callCount["periodic_2"] == 1

            # Run disabled mode for 1 period
            get_test_controller.stepTiming(
                seconds=periodS,
                autonomous=False,
                test=False,
                enabled=False,
            )

            for key, value in robot_with_sim_setup_teardown._callCount.items():
                print(f"{key}:callCount={value}")

            assert robot_with_sim_setup_teardown._callCount["robotPeriodic"] == 5
            assert robot_with_sim_setup_teardown._callCount["periodic_0_0"] == 5
            assert robot_with_sim_setup_teardown._callCount["periodic_0_1"] == 5
            assert robot_with_sim_setup_teardown._callCount["periodic_1"] == 2
            assert robot_with_sim_setup_teardown._callCount["periodic_2"] == 1

            # Run disabled mode for 1 period
            get_test_controller.stepTiming(
                seconds=periodS,
                autonomous=False,
                test=False,
                enabled=False,
            )

            for key, value in robot_with_sim_setup_teardown._callCount.items():
                print(f"{key}:callCount={value}")

            assert robot_with_sim_setup_teardown._callCount["robotPeriodic"] == 6
            assert robot_with_sim_setup_teardown._callCount["periodic_0_0"] == 6
            assert robot_with_sim_setup_teardown._callCount["periodic_0_1"] == 6
            assert robot_with_sim_setup_teardown._callCount["periodic_1"] == 3
            assert robot_with_sim_setup_teardown._callCount["periodic_2"] == 2
            assert robot_with_sim_setup_teardown._callCount["periodic_3"] == 2
            assert robot_with_sim_setup_teardown._callCount["periodic_4"] == 1

            # Run disabled mode for 1 period
            get_test_controller.stepTiming(
                seconds=periodS,
                autonomous=False,
                test=False,
                enabled=False,
            )

            for key, value in robot_with_sim_setup_teardown._callCount.items():
                print(f"{key}:callCount={value}")

            assert robot_with_sim_setup_teardown._callCount["robotPeriodic"] == 7
            assert robot_with_sim_setup_teardown._callCount["periodic_0_0"] == 7
            assert robot_with_sim_setup_teardown._callCount["periodic_0_1"] == 7
            assert robot_with_sim_setup_teardown._callCount["periodic_1"] == 3
            assert robot_with_sim_setup_teardown._callCount["periodic_2"] == 2
            assert robot_with_sim_setup_teardown._callCount["periodic_3"] == 2
            assert robot_with_sim_setup_teardown._callCount["periodic_4"] == 1
            assert robot_with_sim_setup_teardown._callCount["periodic_5"] == 1
