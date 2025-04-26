from enum import Enum

from hal import report, tResourceType, tInstances, observeUserProgramDisabled, \
    observeUserProgramTest, observeUserProgramAutonomous, \
    observeUserProgramTeleop, simPeriodicBefore, simPeriodicAfter
from ntcore import NetworkTableInstance
from wpilib import DriverStation, DSControlWord, Watchdog, LiveWindow, RobotBase, SmartDashboard, reportWarning
from wpilib.shuffleboard import Shuffleboard

_kResourceType_SmartDashboard = tResourceType.kResourceType_SmartDashboard
_kSmartDashboard_LiveWindow = tInstances.kSmartDashboard_LiveWindow

class IterativeRobotMode(Enum):
    kNone = 0
    kDisabled = 1
    kAutonomous = 2
    kTeleop = 3
    kTest = 4

class IterativeRobotPy(RobotBase):

    def __init__(self, period: float):
        super().__init__()
        self._periodS = period
        self._watchdog = Watchdog(self._periodS, self.printLoopOverrunMessage)
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

    def printLoopOverrunMessage(self):
        pass

    def robotInit(self):
        pass

    def driverStationConnected(self):
        pass

    def simulationInit(self):
        pass

    def disabledInit(self):
        pass

    def autonomousInit(self):
        pass

    def teleopInit(self):
        pass

    def testInit(self):
        pass

    def robotPeriodic(self):
        if not self._robotPeriodicHasRun:
            print(f"Default RobotPeriodic() method...Override me!")
            self._robotPeriodicHasRun = True

    def simulationPeriodic(self):
        if not self._simulationPeriodicHasRun:
            print(f"Default simulationPeriodic() method...Override me!")
            self._simulationPeriodicHasRun = True

    def disabledPeriodic(self):
        if not self._disabledPeriodicHasRun:
            print(f"Default disabledPeriodic() method...Override me!")
            self._disabledPeriodicHasRun = True

    def autonomousPeriodic(self):
        if not self._autonomousPeriodicHasRun:
            print(f"Default autonomousPeriodic() method...Override me!")
            self._autonomousPeriodicHasRun = True

    def teleopPeriodic(self):
        if not self._teleopPeriodicHasRun:
            print(f"Default teleopPeriodic() method...Override me!")
            self._teleopPeriodicHasRun = True

    def testPeriodic(self):
        if not self._testPeriodicHasRun:
            print(f"Default testPeriodic() method...Override me!")
            self._teleopPeriodicHasRun = True

    def disabledExit(self):
        pass

    def autonomousExit(self):
        pass

    def teleopExit(self):
        pass

    def testExit(self):
        pass

    # todo @Deprecated(forRemoval=true, since="2025")
    def setNetworkTablesFlushEnabled(self, enabled: bool):
        self._ntFlushEnabled = enabled

    def enableLiveWindowInTest(self, testLW: bool):
        if self.isTestEnabled():
            raise RuntimeError("Can't configure test mode while in test mode!")
        if not self._reportedLw and testLW:
            report(_kResourceType_SmartDashboard, _kSmartDashboard_LiveWindow)
            self._reportedLw = True
        self._lwEnabledInTest = testLW

    def isLiveWindowEnabledInTest(self) -> bool:
        return self._lwEnabledInTest

    def getPeriod(self) -> float:
        return self._periodS

    def loopFunc(self):
        DriverStation.refreshData()
        self._watchdog.reset()

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

            match self._mode:
                case IterativeRobotMode.kDisabled:
                    self.disabledInit()
                    self._watchdog.addEpoch("DisabledInit()")
                case IterativeRobotMode.kAutonomous:
                    self.autonomousInit()
                    self._watchdog.addEpoch("AutonomousInit()")
                case IterativeRobotMode.kTeleop:
                    self.teleopInit()
                    self._watchdog.addEpoch("TeleopInit()")
                case IterativeRobotMode.kTest:
                    if self._lwEnabledInTest:
                        LiveWindow.setEnabled(True)
                        Shuffleboard.enableActuatorWidgets()
                    self.testInit()
                    self._watchdog.addEpoch("TestInit()")
            self._lastMode = self._mode

        # Call the appropriate function depending upon the current robot mode
        match self._mode:
            case IterativeRobotMode.kDisabled:
                observeUserProgramDisabled()
                self.disabledPeriodic()
                self._watchdog.addEpoch("DisabledPeriodic()")
            case IterativeRobotMode.kAutonomous:
                observeUserProgramAutonomous()
                self.autonomousPeriodic()
                self._watchdog.addEpoch("AutonomousPeriodic()")
            case IterativeRobotMode.kTeleop:
                observeUserProgramTeleop()
                self.teleopPeriodic()
                self._watchdog.addEpoch("TeleopPeriodic()")
            case IterativeRobotMode.kTest:
                observeUserProgramTest()
                self.testPeriodic()
                self._watchdog.addEpoch("TestPeriodic()")

        self.robotPeriodic()
        self._watchdog.addEpoch("RobotPeriodic()")

        SmartDashboard.updateValues()
        self._watchdog.addEpoch("SmartDashboard::UpdateValues()")

        LiveWindow.updateValues()
        self._watchdog.addEpoch("LiveWindow::UpdateValues()")

        Shuffleboard.update()
        self._watchdog.addEpoch("Shuffleboard::Update()")

        if self.isSimulation():
            simPeriodicBefore()
            self.simulationPeriodic()
            simPeriodicAfter()
            self._watchdog.addEpoch("SimulationPeriodic()")

        self._watchdog.disable()

        # Flush NetworkTables
        if self._ntFlushEnabled:
            self._networkTableInstanceDefault.flushLocal()

        # Warn on loop time overruns
        if self._watchdog.isExpired():
            self._watchdog.printEpochs()

    def printLoopOverrunMessages(self):
        reportWarning(
            f"Loop time of {self._periodS}s overrun\n", False
        )

    def printWatchdogEpochs(self):
        self._watchdog.printEpochs()
