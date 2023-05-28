# Don't import stuff from the package here, it'll cause a circular import

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from .command import Command
    from .commandscheduler import CommandScheduler

from wpiutil import Sendable, SendableBuilder, SendableRegistry


class Subsystem(Sendable):
    """
    A robot subsystem. Subsystems are the basic unit of robot organization in the Command-based
    framework; they encapsulate low-level hardware objects (motor controllers, sensors, etc.) and
    provide methods through which they can be used by Commands. Subsystems are used by the
    CommandScheduler's resource management system to ensure multiple robot actions are not
    "fighting" over the same hardware; Commands that use a subsystem should include that subsystem in
    their Command#getRequirements() method, and resources used within a subsystem should
    generally remain encapsulated and not be shared by other parts of the robot.

    Subsystems must be registered with the scheduler with the {@link
    CommandScheduler#registerSubsystem(Subsystem...)} method in order for the {@link
    Subsystem#periodic()} method to be called. It is recommended that this method be called from the
    constructor of users' Subsystem implementations. The SubsystemBase class offers a simple
    base for user implementations that handles this.
    """

    def __new__(cls, *arg, **kwargs) -> "Subsystem":
        instance = super().__new__(cls)
        super().__init__(instance)
        SendableRegistry.addLW(instance, cls.__name__, cls.__name__)
        # add to the scheduler
        from .commandscheduler import CommandScheduler

        CommandScheduler.getInstance().registerSubsystem(instance)
        return instance

    def __init__(self) -> None:
        pass

    def periodic(self) -> None:
        """
        This method is called periodically by the CommandScheduler. Useful for updating
        subsystem-specific state that you don't want to offload to a Command. Teams should try
        to be consistent within their own codebases about which responsibilities will be handled by
        Commands, and which will be handled here."""
        pass

    def simulationPeriodic(self) -> None:
        """
        This method is called periodically by the CommandScheduler. Useful for updating
        subsystem-specific state that needs to be maintained for simulations, such as for updating
        edu.wpi.first.wpilibj.simulation classes and setting simulated sensor readings.
        """
        pass

    def setDefaultCommand(self, command: Command) -> None:
        """
        Sets the default Command of the subsystem. The default command will be automatically
        scheduled when no other commands are scheduled that require the subsystem. Default commands
        should generally not end on their own, i.e. their Command#isFinished() method should
        always return false. Will automatically register this subsystem with the {@link
        CommandScheduler}.

        :param defaultCommand: the default command to associate with this subsystem"""
        from .commandscheduler import CommandScheduler

        CommandScheduler.getInstance().setDefaultCommand(self, command)

    def removeDefaultCommand(self) -> None:
        """
        Removes the default command for the subsystem. This will not cancel the default command if it
        is currently running."""
        CommandScheduler.getInstance().removeDefaultCommand(self)

    def getDefaultCommand(self) -> Optional[Command]:
        """
        Gets the default command for this subsystem. Returns null if no default command is currently
        associated with the subsystem.

        :returns: the default command associated with this subsystem"""
        from .commandscheduler import CommandScheduler

        return CommandScheduler.getInstance().getDefaultCommand(self)

    def getCurrentCommand(self) -> Optional[Command]:
        """
        Returns the command currently running on this subsystem. Returns null if no command is
        currently scheduled that requires this subsystem.

        :returns: the scheduled command currently requiring this subsystem"""
        from .commandscheduler import CommandScheduler

        return CommandScheduler.getInstance().requiring(self)

    def runOnce(self, action: Callable[[], None]) -> Command:
        """
        Constructs a command that runs an action once and finishes. Requires this subsystem.

        :param action: the action to run
        :return: the command"""
        from .cmd import runOnce

        return runOnce(action, self)

    def run(self, action: Callable[[], None]) -> Command:
        """
        Constructs a command that runs an action every iteration until interrupted. Requires this
        subsystem.

        :param action: the action to run
        :returns: the command"""
        from .cmd import run

        return run(action, self)

    def startEnd(self, start: Callable[[], None], end: Callable[[], None]) -> Command:
        """
        Constructs a command that runs an action once and another action when the command is
        interrupted. Requires this subsystem.

        :param start: the action to run on start
        :param end: the action to run on interrupt
        :returns: the command"""
        from .cmd import startEnd

        return startEnd(start, end, self)

    def runEnd(self, run: Callable[[], None], end: Callable[[], None]) -> Command:
        """
        Constructs a command that runs an action every iteration until interrupted, and then runs a
        second action. Requires this subsystem.

        :param run: the action to run every iteration
        :param end: the action to run on interrupt
        :returns: the command"""
        from .cmd import runEnd

        return runEnd(run, end, self)

    def getName(self) -> str:
        return SendableRegistry.getName(self)

    def setName(self, name: str) -> None:
        SendableRegistry.setName(self, name)

    def getSubsystem(self) -> str:
        return SendableRegistry.getSubsystem(self)

    def addChild(self, name: str, child: Sendable) -> None:
        SendableRegistry.addLW(child, self.getSubsystem(), name)

    def initSendable(self, builder: SendableBuilder) -> None:
        builder.setSmartDashboardType("Subsystem")

        builder.addBooleanProperty(
            ".hasDefault", lambda: self.getDefaultCommand() is not None, lambda _: None
        )

        def get_default():
            command = self.getDefaultCommand()
            if command is not None:
                return command.getName()
            return "none"

        builder.addStringProperty(".default", get_default, lambda _: None)
        builder.addBooleanProperty(
            ".hasCommand", lambda: self.getCurrentCommand() is not None, lambda _: None
        )

        def get_current():
            command = self.getCurrentCommand()
            if command is not None:
                return command.getName()
            return "none"

        builder.addStringProperty(".command", get_current, lambda _: None)
