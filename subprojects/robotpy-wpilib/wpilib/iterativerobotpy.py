import hal
import ntcore
import wpilib
import wpilib._impl
import wpilib._impl.report_error


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
        self._m_word = wpilib.DSControlWord()
        self._m_period = period
        self._m_watchdog = wpilib.Watchdog(self._m_period, self.printLoopOverrunMessage)
        self._mode: IterativeRobotMode = IterativeRobotMode.kNone
        self._m_lastMode: IterativeRobotMode = IterativeRobotMode.kNone
        self._m_ntFlushEnabled: bool = True
        self._m_lwEnabledInTest: bool = False
        self._m_calledDsConnected: bool = False
        self._m_reportedLw: bool = False
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
        self._m_ntFlushEnabled = enabled

    def enableLiveWindowInTest(self, testLW: bool):
        if self.isTestEnabled():
            pass
            # todo throw
            #     throw FRC_MakeError(err::IncompatibleMode,
            #                         "Can't configure test mode while in test mode!")
        if not self._m_reportedLw and testLW:
            hal.report(
                hal.tResourceType.kResourceType_SmartDashboard,
                hal.tInstances.kSmartDashboard_LiveWindow,
            )
            self._m_reportedLw = True
        self._m_lwEnabledInTest = testLW

    def isLiveWindowEnabledInTest(self) -> bool:
        return self._m_lwEnabledInTest

    def getPeriod(self) -> float:
        return self._m_period

    def loopFunc(self):
        wpilib.DriverStation.refreshData()
        self._m_watchdog.reset()

        self._m_word.refresh()  # todo from Java implementation

        mode = IterativeRobotMode.kNone
        if self._m_word.IsDisabled():
            mode = IterativeRobotMode.kDisabled
        elif self._m_word.IsAutonomous():
            mode = IterativeRobotMode.kAutonomous
        elif self._m_word.IsTeleop():
            mode = IterativeRobotMode.kTeleop
        elif self._m_word.IsTest():
            mode = IterativeRobotMode.kTest

        if not self._m_calledDsConnected and self._m_word.IsDSAttached():
            self._m_calledDsConnected = True
            self.driverStationConnected()

        # If mode changed, call mode exit and entry functions
        if self._m_lastMode != mode:
            if self._m_lastMode == IterativeRobotMode.kDisabled:
                self.disabledExit()
            elif self._m_lastMode == IterativeRobotMode.kAutonomous:
                self.autonomousExit()
            elif self._m_lastMode == IterativeRobotMode.kTeleop:
                self.teleopExit()
            elif self._m_lastMode == IterativeRobotMode.kTest:
                if self._m_lwEnabledInTest:
                    wpilib.LiveWindow.setEnabled(False)
                    # todo Shuffleboard::DisableActuatorWidgets()
                self.testExit()

        if mode == IterativeRobotMode.kDisabled:
            self.disabledInit()
            self._m_watchdog.addEpoch("DisabledInit()")
        elif mode == IterativeRobotMode.kAutonomous:
            self.autonomousInit()
            self._m_watchdog.addEpoch("AutonomousInit()")
        elif mode == IterativeRobotMode.kTeleop:
            self.teleopInit()
            self._m_watchdog.addEpoch("TeleopInit()")
        elif mode == IterativeRobotMode.kTest:
            if self._m_lwEnabledInTest:
                wpilib.LiveWindow.setEnabled(True)
                # todo Shuffleboard::EnableActuatorWidgets()
            self.testInit()
            self._m_watchdog.addEpoch("TestInit()")
        self._m_lastMode = mode

        # Call the appropriate function depending upon the current robot mode
        if mode == IterativeRobotMode.kDisabled:
            hal.observeUserProgramDisabled()
            self.disabledPeriodic()
            self._m_watchdog.addEpoch("DisabledPeriodic()")
        elif mode == IterativeRobotMode.kAutonomous:
            hal.observeUserProgramAutonomous()
            self.autonomousPeriodic()
            self._m_watchdog.addEpoch("AutonomousPeriodic()")
        elif mode == IterativeRobotMode.kTeleop:
            hal.observeUserProgramTeleop()
            self.teleopPeriodic()
            self._m_watchdog.addEpoch("TeleopPeriodic()")
        elif mode == IterativeRobotMode.kTest:
            hal.observeUserProgramTest()
            self.testPeriodic()
            self._m_watchdog.addEpoch("TestPeriodic()")

        self.robotPeriodic()
        self._m_watchdog.addEpoch("RobotPeriodic()")
        #
        wpilib.SmartDashboard.updateValues()
        self._m_watchdog.addEpoch("SmartDashboard::UpdateValues()")
        wpilib.LiveWindow.updateValues()
        self._m_watchdog.addEpoch("LiveWindow::UpdateValues()")
        # todo Shuffleboard::Update()
        self._m_watchdog.addEpoch("Shuffleboard::Update()")
        if self.isSimulation():
            hal.simPeriodicBefore()
            self.simulationPeriodic()
            hal.simPeriodicAfter()
            self._m_watchdog.addEpoch("SimulationPeriodic()")

        self._m_watchdog.Disable()

        # // Flush NetworkTables
        if self._m_ntFlushEnabled:
            ntcore.NetworkTableInstance.getDefault().flushLocal()

        # Warn on loop time overruns
        if self._m_watchdog.IsExpired():
            self._m_watchdog.PrintEpochs()

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
            f"Loop time of {self._m_period}s overrun\n", False
        )

    def printWatchdogEpochs(self):
        self._m_watchdog.printEpochs()
