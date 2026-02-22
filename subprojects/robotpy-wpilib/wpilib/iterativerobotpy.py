from enum import Enum

from hal import (
    report,
    tResourceType,
    tInstances,
    observeUserProgramDisabled,
    observeUserProgramTest,
    observeUserProgramAutonomous,
    observeUserProgramTeleop,
    simPeriodicBefore,
    simPeriodicAfter,
)
from ntcore import NetworkTableInstance
from wpilib import (
    DriverStation,
    DSControlWord,
    Watchdog,
    LiveWindow,
    RobotBase,
    SmartDashboard,
    reportWarning,
)
from wpilib.shuffleboard import Shuffleboard
import wpimath.units

_kResourceType_SmartDashboard = tResourceType.kResourceType_SmartDashboard
_kSmartDashboard_LiveWindow = tInstances.kSmartDashboard_LiveWindow


class IterativeRobotMode(Enum):
    kNone = 0
    kDisabled = 1
    kAutonomous = 2
    kTeleop = 3
    kTest = 4


# todo should this be IterativeRobotPy or IterativeRobotBase (replacing) or IterativeRobotBasePy
class IterativeRobotPy(RobotBase):
    """
    IterativeRobotPy implements a specific type of robot program framework,
    extending the RobotBase class. It provides similar functionality as
    IterativeRobotBase does in a python wrapper of C++, but in pure python.

    The IterativeRobotPy class does not implement StartCompetition(), so it
    should not be used by teams directly.

    This class provides the following functions which are called by the main
    loop, StartCompetition(), at the appropriate times:

    robotInit() -- provide for initialization at robot power-on

    DriverStationConnected() -- provide for initialization the first time the DS
    is connected

    Init() functions -- each of the following functions is called once when the
    appropriate mode is entered:

    - disabledInit() -- called each and every time disabled is entered from another mode
    - autonomousInit() -- called each and every time autonomous is entered from another mode
    - teleopInit() -- called each and every time teleop is entered from another mode
    - testInit() -- called each and every time test is entered from another mode

    Periodic() functions -- each of these functions is called on an interval:

    - robotPeriodic()
    - disabledPeriodic()
    - autonomousPeriodic()
    - teleopPeriodic()
    - testPeriodic()

    Exit() functions -- each of the following functions is called once when the
    appropriate mode is exited:

    - disabledExit() -- called each and every time disabled is exited
    - autonomousExit() -- called each and every time autonomous is exited
    - teleopExit() -- called each and every time teleop is exited
    - testExit() -- called each and every time test is exited
    """

    def __init__(self, period: wpimath.units.seconds) -> None:
        """
        Constructor for IterativeRobotPy.

        :param period: period of the main robot periodic loop in seconds.
        """
        super().__init__()
        self._periodS = period
        self.watchdog = Watchdog(self._periodS, self.printLoopOverrunMessage)
        self._networkTableInstanceDefault = NetworkTableInstance.getDefault()
        self._mode: IterativeRobotMode = IterativeRobotMode.kNone
        self._lastMode: IterativeRobotMode = IterativeRobotMode.kNone
        self._ntFlushEnabled: bool = True
        self._lwEnabledInTest: bool = False
        self._calledDsConnected: bool = False
        self._reportedLw: bool = False
        self._robotPeriodicHasRun: bool = False
        self._simulationPeriodicHasRun: bool = False
        self._disabledPeriodicHasRun: bool = False
        self._autonomousPeriodicHasRun: bool = False
        self._teleopPeriodicHasRun: bool = False
        self._testPeriodicHasRun: bool = False

    def robotInit(self) -> None:
        """
        Robot-wide initialization code should go here.

        Users should override this method for default Robot-wide initialization
        which will be called when the robot is first powered on. It will be called
        exactly one time.

        Note: This method is functionally identical to the class constructor so
        that should be used instead.
        """
        pass

    def driverStationConnected(self) -> None:
        """
        Code that needs to know the DS state should go here.

        Users should override this method for initialization that needs to occur
        after the DS is connected, such as needing the alliance information.
        """
        pass

    def _simulationInit(self) -> None:
        """
        Robot-wide simulation initialization code should go here.

        Users should override this method for default Robot-wide simulation
        related initialization which will be called when the robot is first
        started. It will be called exactly one time after robotInit is called
        only when the robot is in simulation.
        """
        pass

    def disabledInit(self) -> None:
        """
        Initialization code for disabled mode should go here.

        Users should override this method for initialization code which will be
        called each time
        the robot enters disabled mode.
        """
        pass

    def autonomousInit(self) -> None:
        """
        Initialization code for autonomous mode should go here.

        Users should override this method for initialization code which will be
        called each time the robot enters autonomous mode.
        """
        pass

    def teleopInit(self) -> None:
        """
        Initialization code for teleop mode should go here.

        Users should override this method for initialization code which will be
        called each time the robot enters teleop mode.
        """
        pass

    def testInit(self) -> None:
        """
        Initialization code for test mode should go here.

        Users should override this method for initialization code which will be
        called each time the robot enters test mode.
        """
        pass

    def robotPeriodic(self) -> None:
        """
        Periodic code for all modes should go here.

        This function is called each time a new packet is received from the driver
        station.
        """
        if not self._robotPeriodicHasRun:
            print(f"Default robotPeriodic() method... Override me!")
            self._robotPeriodicHasRun = True

    def _simulationPeriodic(self) -> None:
        """
        Periodic simulation code should go here.

        This function is called in a simulated robot after user code executes.
        """
        if not self._simulationPeriodicHasRun:
            print(f"Default _simulationPeriodic() method... Override me!")
            self._simulationPeriodicHasRun = True

    def disabledPeriodic(self) -> None:
        """
        Periodic code for disabled mode should go here.

        Users should override this method for code which will be called each time a
        new packet is received from the driver station and the robot is in disabled
        mode.
        """
        if not self._disabledPeriodicHasRun:
            print(f"Default disabledPeriodic() method... Override me!")
            self._disabledPeriodicHasRun = True

    def autonomousPeriodic(self) -> None:
        """
        Periodic code for autonomous mode should go here.

        Users should override this method for code which will be called each time a
        new packet is received from the driver station and the robot is in
        autonomous mode.
        """
        if not self._autonomousPeriodicHasRun:
            print(f"Default autonomousPeriodic() method... Override me!")
            self._autonomousPeriodicHasRun = True

    def teleopPeriodic(self) -> None:
        """
        Periodic code for teleop mode should go here.

        Users should override this method for code which will be called each time a
        new packet is received from the driver station and the robot is in teleop
        mode.
        """
        if not self._teleopPeriodicHasRun:
            print(f"Default teleopPeriodic() method... Override me!")
            self._teleopPeriodicHasRun = True

    def testPeriodic(self) -> None:
        """
        Periodic code for test mode should go here.

        Users should override this method for code which will be called each time a
        new packet is received from the driver station and the robot is in test
        mode.
        """
        if not self._testPeriodicHasRun:
            print(f"Default testPeriodic() method... Override me!")
            self._testPeriodicHasRun = True

    def disabledExit(self) -> None:
        """
        Exit code for disabled mode should go here.

        Users should override this method for code which will be called each time
        the robot exits disabled mode.
        """
        pass

    def autonomousExit(self) -> None:
        """
        Exit code for autonomous mode should go here.

        Users should override this method for code which will be called each time
        the robot exits autonomous mode.
        """
        pass

    def teleopExit(self) -> None:
        """
        Exit code for teleop mode should go here.

        Users should override this method for code which will be called each time
        the robot exits teleop mode.
        """
        pass

    def testExit(self) -> None:
        """
        Exit code for test mode should go here.

        Users should override this method for code which will be called each time
        the robot exits test mode.
        """
        pass

    def setNetworkTablesFlushEnabled(self, enabled: bool) -> None:
        """
        Enables or disables flushing NetworkTables every loop iteration.
        By default, this is enabled.

        :deprecated: Deprecated without replacement.

        :param enabled: True to enable, false to disable.
        """

        self._ntFlushEnabled = enabled

    def enableLiveWindowInTest(self, testLW: bool) -> None:
        """
        Sets whether LiveWindow operation is enabled during test mode.

        :param testLW: True to enable, false to disable. Defaults to false.
                       @throws if called in test mode.
        """
        if self.isTestEnabled():
            raise RuntimeError("Can't configure test mode while in test mode!")
        if not self._reportedLw and testLW:
            report(_kResourceType_SmartDashboard, _kSmartDashboard_LiveWindow)
            self._reportedLw = True
        self._lwEnabledInTest = testLW

    def isLiveWindowEnabledInTest(self) -> bool:
        """
        Whether LiveWindow operation is enabled during test mode.
        """
        return self._lwEnabledInTest

    def getPeriod(self) -> wpimath.units.seconds:
        """
        Gets time period between calls to Periodic() functions.
        """
        return self._periodS

    def _loopFunc(self) -> None:
        """
        Loop function.
        """
        DriverStation.refreshData()
        self.watchdog.reset()

        isEnabled, isAutonomous, isTest = self.getControlState()
        if not isEnabled:
            self._mode = IterativeRobotMode.kDisabled
        elif isAutonomous:
            self._mode = IterativeRobotMode.kAutonomous
        elif isTest:
            self._mode = IterativeRobotMode.kTest
        else:
            self._mode = IterativeRobotMode.kTeleop

        if not self._calledDsConnected and DSControlWord().isDSAttached():
            self._calledDsConnected = True
            self.driverStationConnected()

        # If self._mode changed, call self._mode exit and entry functions
        if self._lastMode is not self._mode:

            if self._lastMode is IterativeRobotMode.kDisabled:
                self.disabledExit()
            elif self._lastMode is IterativeRobotMode.kAutonomous:
                self.autonomousExit()
            elif self._lastMode is IterativeRobotMode.kTeleop:
                self.teleopExit()
            elif self._lastMode is IterativeRobotMode.kTest:
                if self._lwEnabledInTest:
                    LiveWindow.setEnabled(False)
                    Shuffleboard.disableActuatorWidgets()
                self.testExit()
            """
            todo switch to match statements when we don't build with python 3.9
            match self._lastMode:
                case IterativeRobotMode.kDisabled:
                    self.disabledExit()
                case IterativeRobotMode.kAutonomous:
                    self.autonomousExit()
                case IterativeRobotMode.kTeleop:
                    self.teleopExit()
                case IterativeRobotMode.kTest:
                    if self._lwEnabledInTest:
                        LiveWindow.setEnabled(False)
                        Shuffleboard.disableActuatorWidgets()
                    self.testExit()
            """

            if self._mode is IterativeRobotMode.kDisabled:
                self.disabledInit()
                self.watchdog.addEpoch("disabledInit()")
            elif self._mode is IterativeRobotMode.kAutonomous:
                self.autonomousInit()
                self.watchdog.addEpoch("autonomousInit()")
            elif self._mode is IterativeRobotMode.kTeleop:
                self.teleopInit()
                self.watchdog.addEpoch("teleopInit()")
            elif self._mode is IterativeRobotMode.kTest:
                if self._lwEnabledInTest:
                    LiveWindow.setEnabled(True)
                    Shuffleboard.enableActuatorWidgets()
                self.testInit()
                self.watchdog.addEpoch("testInit()")
            """
            match self._mode:
                case IterativeRobotMode.kDisabled:
                    self.disabledInit()
                    self._watchdog.addEpoch("disabledInit()")
                case IterativeRobotMode.kAutonomous:
                    self.autonomousInit()
                    self._watchdog.addEpoch("autonomousInit()")
                case IterativeRobotMode.kTeleop:
                    self.teleopInit()
                    self._watchdog.addEpoch("teleopInit()")
                case IterativeRobotMode.kTest:
                    if self._lwEnabledInTest:
                        LiveWindow.setEnabled(True)
                        Shuffleboard.enableActuatorWidgets()
                    self.testInit()
                    self._watchdog.addEpoch("testInit()")
            """
            self._lastMode = self._mode

        # Call the appropriate function depending upon the current robot mode
        if self._mode is IterativeRobotMode.kDisabled:
            observeUserProgramDisabled()
            self.disabledPeriodic()
            self.watchdog.addEpoch("disabledPeriodic()")
        elif self._mode is IterativeRobotMode.kAutonomous:
            observeUserProgramAutonomous()
            self.autonomousPeriodic()
            self.watchdog.addEpoch("autonomousPeriodic()")
        elif self._mode is IterativeRobotMode.kTeleop:
            observeUserProgramTeleop()
            self.teleopPeriodic()
            self.watchdog.addEpoch("teleopPeriodic()")
        elif self._mode is IterativeRobotMode.kTest:
            observeUserProgramTest()
            self.testPeriodic()
            self.watchdog.addEpoch("testPeriodic()")
        """
        match self._mode:
            case IterativeRobotMode.kDisabled:
                observeUserProgramDisabled()
                self.disabledPeriodic()
                self.watchdog.addEpoch("disabledPeriodic()")
            case IterativeRobotMode.kAutonomous:
                observeUserProgramAutonomous()
                self.autonomousPeriodic()
                self.watchdog.addEpoch("autonomousPeriodic()")
            case IterativeRobotMode.kTeleop:
                observeUserProgramTeleop()
                self.teleopPeriodic()
                self.watchdog.addEpoch("teleopPeriodic()")
            case IterativeRobotMode.kTest:
                observeUserProgramTest()
                self.testPeriodic()
                self.watchdog.addEpoch("testPeriodic()")
        """

        self.robotPeriodic()
        self.watchdog.addEpoch("robotPeriodic()")

        SmartDashboard.updateValues()
        self.watchdog.addEpoch("SmartDashboard.updateValues()")

        LiveWindow.updateValues()
        self.watchdog.addEpoch("LiveWindow.updateValues()")

        Shuffleboard.update()
        self.watchdog.addEpoch("Shuffleboard.update()")

        if self.isSimulation():
            simPeriodicBefore()
            self._simulationPeriodic()
            simPeriodicAfter()
            self.watchdog.addEpoch("_simulationPeriodic()")

        self.watchdog.disable()

        # Flush NetworkTables
        if self._ntFlushEnabled:
            self._networkTableInstanceDefault.flushLocal()

        # Warn on loop time overruns
        if self.watchdog.isExpired():
            self.printWatchdogEpochs()

    def printLoopOverrunMessage(self) -> None:
        reportWarning(f"Loop time of {self.watchdog.getTimeout()}s overrun", False)

    def printWatchdogEpochs(self) -> None:
        """
        Prints list of epochs added so far and their times.
        """
        self.watchdog.printEpochs()
