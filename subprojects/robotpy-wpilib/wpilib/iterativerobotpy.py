import hal
import ntcore
import wpilib
import wpilib._impl
import wpilib._impl.report_error

from wpilib import DriverStation, DSControlWord
from wpilib.shuffleboard import Shuffleboard


from enum import IntEnum


class IterativeRobotMode(IntEnum):
    kNone = 0
    kDisabled = 1
    kAutonomous = 2
    kTeleop = 3
    kTest = 4


class IterativeRobotPy(wpilib.RobotBase):

    def __init__(self, period: float):
        super().__init__()
        self._word = DSControlWord()
        self._periodS = period
        self._watchdog = wpilib.Watchdog(self._periodS, self.printLoopOverrunMessage)
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
            pass
            # todo throw
            #     throw FRC_MakeError(err::IncompatibleMode,
            #                         "Can't configure test mode while in test mode!")
        if not self._reportedLw and testLW:
            hal.report(
                hal.tResourceType.kResourceType_SmartDashboard,
                hal.tInstances.kSmartDashboard_LiveWindow,
            )
            self._reportedLw = True
        self._lwEnabledInTest = testLW

    def isLiveWindowEnabledInTest(self) -> bool:
        return self._lwEnabledInTest

    def getPeriod(self) -> float:
        return self._periodS

    def loopFunc(self):
        DriverStation.refreshData()
        self._watchdog.reset()

        self._word = DSControlWord() # todo switch to a version that does refresh()

        self._mode = IterativeRobotMode.kNone
        if self._word.isDisabled():
            self._mode = IterativeRobotMode.kDisabled
        elif self._word.isAutonomous():
            self._mode = IterativeRobotMode.kAutonomous
        elif self._word.isTeleop():
            self._mode = IterativeRobotMode.kTeleop
        elif self._word.isTest():
            self._mode = IterativeRobotMode.kTest

        if not self._calledDsConnected and self._word.isDSAttached():
            self._calledDsConnected = True
            self.driverStationConnected()

        # If self._mode changed, call self._mode exit and entry functions
        if self._lastMode != self._mode:
            if self._lastMode == IterativeRobotMode.kDisabled:
                self.disabledExit()
            elif self._lastMode == IterativeRobotMode.kAutonomous:
                self.autonomousExit()
            elif self._lastMode == IterativeRobotMode.kTeleop:
                self.teleopExit()
            elif self._lastMode == IterativeRobotMode.kTest:
                if self._lwEnabledInTest:
                    wpilib.LiveWindow.setEnabled(False)
                    Shuffleboard.disableActuatorWidgets()
                self.testExit()

            if self._mode == IterativeRobotMode.kDisabled:
                self.disabledInit()
                self._watchdog.addEpoch("DisabledInit()")
            elif self._mode == IterativeRobotMode.kAutonomous:
                self.autonomousInit()
                self._watchdog.addEpoch("AutonomousInit()")
            elif self._mode == IterativeRobotMode.kTeleop:
                self.teleopInit()
                self._watchdog.addEpoch("TeleopInit()")
            elif self._mode == IterativeRobotMode.kTest:
                if self._lwEnabledInTest:
                    wpilib.LiveWindow.setEnabled(True)
                    Shuffleboard.enableActuatorWidgets()
                self.testInit()
                self._watchdog.addEpoch("TestInit()")
            self._lastMode = self._mode

        # Call the appropriate function depending upon the current robot mode
        if self._mode == IterativeRobotMode.kDisabled:
            hal.observeUserProgramDisabled()
            self.disabledPeriodic()
            self._watchdog.addEpoch("DisabledPeriodic()")
        elif self._mode == IterativeRobotMode.kAutonomous:
            hal.observeUserProgramAutonomous()
            self.autonomousPeriodic()
            self._watchdog.addEpoch("AutonomousPeriodic()")
        elif self._mode == IterativeRobotMode.kTeleop:
            hal.observeUserProgramTeleop()
            self.teleopPeriodic()
            self._watchdog.addEpoch("TeleopPeriodic()")
        elif self._mode == IterativeRobotMode.kTest:
            hal.observeUserProgramTest()
            self.testPeriodic()
            self._watchdog.addEpoch("TestPeriodic()")

        self.robotPeriodic()
        self._watchdog.addEpoch("RobotPeriodic()")
        #
        wpilib.SmartDashboard.updateValues()
        self._watchdog.addEpoch("SmartDashboard::UpdateValues()")
        wpilib.LiveWindow.updateValues()
        self._watchdog.addEpoch("LiveWindow::UpdateValues()")
        Shuffleboard.update()
        self._watchdog.addEpoch("Shuffleboard::Update()")
        if self.isSimulation():
            hal.simPeriodicBefore()
            self.simulationPeriodic()
            hal.simPeriodicAfter()
            self._watchdog.addEpoch("SimulationPeriodic()")

        self._watchdog.disable()

        # // Flush NetworkTables
        if self._ntFlushEnabled:
            ntcore.NetworkTableInstance.getDefault().flushLocal()

        # Warn on loop time overruns
        if self._watchdog.isExpired():
            self._watchdog.printEpochs()

    def printLoopOverrunMessages(self):
        # todo ask about this
        # cpp has this as a error, java as a warning, is this the right way to call?
        # void IterativeRobotBase::PrintLoopOverrunMessage() {
        #     FRC_ReportError(err::Error, "Loop time of {:.6f}s overrun", m_period.value())
        # }
        # private void printLoopOverrunMessage() {
        #     DriverStation.reportWarning("Loop time of " + m_period + "s overrun\n", false);
        # }
        wpilib._impl.report_error.reportWarning(
            f"Loop time of {self._periodS}s overrun\n", False
        )

    def printWatchdogEpochs(self):
        self._watchdog.printEpochs()
