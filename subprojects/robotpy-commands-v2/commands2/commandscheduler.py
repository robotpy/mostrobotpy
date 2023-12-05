from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Union

import hal
from typing_extensions import Self
from wpilib import RobotBase, RobotState, TimedRobot, Watchdog
from wpilib.event import EventLoop

from .command import Command, InterruptionBehavior
from .commandgroup import *
from .subsystem import Subsystem


class CommandScheduler:
    """
    The scheduler responsible for running Commands. A Command-based robot should call {@link
    CommandScheduler#run()} on the singleton instance in its periodic block in order to run commands
    synchronously from the main loop. Subsystems should be registered with the scheduler using {@link
    CommandScheduler#registerSubsystem(Subsystem...)} in order for their Subsystem#periodic()
    methods to be called and for their default commands to be scheduled.
    """

    _instance: Optional[CommandScheduler] = None

    def __new__(cls) -> CommandScheduler:
        if cls._instance is None:
            return super().__new__(cls)
        return cls._instance

    @staticmethod
    def getInstance() -> "CommandScheduler":
        """
        Returns the Scheduler instance.

        :returns: the instance
        """
        return CommandScheduler()

    @staticmethod
    def resetInstance() -> None:
        """
        Resets the scheduler instance, which is useful for testing purposes. This should not be
        called by user code.
        """
        inst = CommandScheduler._instance
        if inst:
            inst._defaultButtonLoop.clear()
        CommandScheduler._instance = None

    def __init__(self) -> None:
        """
        Gets the scheduler instance.
        """
        if CommandScheduler._instance is not None:
            return
        CommandScheduler._instance = self
        self._composedCommands: Set[Command] = set()
        self._scheduledCommands: Dict[Command, None] = {}
        self._requirements: Dict[Subsystem, Command] = {}
        self._subsystems: Dict[Subsystem, Optional[Command]] = {}

        self._defaultButtonLoop = EventLoop()
        self.setActiveButtonLoop(self._defaultButtonLoop)

        self._disabled = False

        self._initActions: List[Callable[[Command], None]] = []
        self._executeActions: List[Callable[[Command], None]] = []
        self._interruptActions: List[Callable[[Command], None]] = []
        self._finishActions: List[Callable[[Command], None]] = []

        self._inRunLoop = False
        self._toSchedule: Dict[Command, None] = {}
        self._toCancel: Dict[Command, None] = {}

        self._watchdog = Watchdog(TimedRobot.kDefaultPeriod, lambda: None)

        hal.report(
            hal.tResourceType.kResourceType_Command.value,
            hal.tInstances.kCommand2_Scheduler.value,
        )

    def setPeriod(self, period: float) -> None:
        """
        Changes the period of the loop overrun watchdog. This should be kept in sync with the
        TimedRobot period.

        :param period: Period in seconds.
        """
        self._watchdog.setTimeout(period)

    def getDefaultButtonLoop(self) -> EventLoop:
        """
        Get the default button poll.

        :returns: a reference to the default EventLoop object polling buttons.
        """
        return self._defaultButtonLoop

    def getActiveButtonLoop(self) -> EventLoop:
        """
        Get the active button poll.

        :returns: a reference to the current EventLoop object polling buttons.
        """
        return self._activeButtonLoop

    def setActiveButtonLoop(self, loop: EventLoop) -> None:
        """
        Replace the button poll with another one.

        :param loop: the new button polling loop object.
        """
        self._activeButtonLoop = loop

    def initCommand(self, command: Command, *requirements: Subsystem) -> None:
        """
        Initializes a given command, adds its requirements to the list, and performs the init actions.

        :param command: The command to initialize
        :param requirements: The command requirements
        """
        self._scheduledCommands[command] = None
        for requirement in requirements:
            self._requirements[requirement] = command
        command.initialize()
        for action in self._initActions:
            action(command)
        # self._watchdog.addEpoch()

    def schedule(self, *commands) -> None:
        """
        Schedules a command for execution. Does nothing if the command is already scheduled. If a
        command's requirements are not available, it will only be started if all the commands currently
        using those requirements have been scheduled as interruptible. If this is the case, they will
        be interrupted and the command will be scheduled.

        :param commands: the commands to schedule.
        """
        if len(commands) > 1:
            for command in commands:
                self.schedule(command)
            return

        command = commands[0]

        if command is None:
            # DriverStation.reportWarning("CommandScheduler tried to schedule a null command!", True)
            return

        if self._inRunLoop:
            self._toSchedule[command] = None
            return

        if command in self.getComposedCommands():
            raise IllegalCommandUse(
                "A command that is part of a CommandGroup cannot be independently scheduled"
            )

        if self._disabled:
            return

        if RobotState.isDisabled() and not command.runsWhenDisabled():
            return

        if self.isScheduled(command):
            return

        requirements = command.getRequirements()

        if self._requirements.keys().isdisjoint(requirements):
            self.initCommand(command, *requirements)
        else:
            for requirement in requirements:
                requiringCommand = self.requiring(requirement)
                if (
                    requiringCommand is not None
                    and requiringCommand.getInterruptionBehavior()
                    == InterruptionBehavior.kCancelIncoming
                ):
                    return

            for requirement in requirements:
                requiringCommand = self.requiring(requirement)
                if requiringCommand is not None:
                    self.cancel(requiringCommand)

            self.initCommand(command, *requirements)

    def run(self):
        """
        Runs a single iteration of the scheduler. The execution occurs in the following order:

        Subsystem periodic methods are called.

        Button bindings are polled, and new commands are scheduled from them.

        Currently-scheduled commands are executed.

        End conditions are checked on currently-scheduled commands, and commands that are finished
        have their end methods called and are removed.

        Any subsystems not being used as requirements have their default methods started.
        """
        if self._disabled:
            return
        self._watchdog.reset()

        for subsystem in self._subsystems:
            subsystem.periodic()
            if RobotBase.isSimulation():
                subsystem.simulationPeriodic()
            # self._watchdog.addEpoch()

        loopCache = self._activeButtonLoop
        loopCache.poll()
        self._watchdog.addEpoch("buttons.run()")

        self._inRunLoop = True

        for command in self._scheduledCommands.copy():
            if not command.runsWhenDisabled() and RobotState.isDisabled():
                command.end(True)
                for action in self._interruptActions:
                    action(command)
                for requirement in command.getRequirements():
                    self._requirements.pop(requirement)
                self._scheduledCommands.pop(command)
                continue

            command.execute()
            for action in self._executeActions:
                action(command)
            # self._watchdog.addEpoch()
            if command.isFinished():
                command.end(False)
                for action in self._finishActions:
                    action(command)
                self._scheduledCommands.pop(command)
                for requirement in command.getRequirements():
                    self._requirements.pop(requirement)

        self._inRunLoop = False

        for command in self._toSchedule:
            self.schedule(command)

        for command in self._toCancel:
            self.cancel(command)

        self._toSchedule.clear()
        self._toCancel.clear()

        for subsystem, command in self._subsystems.items():
            if subsystem not in self._requirements and command is not None:
                self.schedule(command)

        self._watchdog.disable()
        if self._watchdog.isExpired():
            self._watchdog.printEpochs()

    def registerSubsystem(self, *subsystems: Subsystem) -> None:
        """
        Registers subsystems with the scheduler. This must be called for the subsystem's periodic block
        to run when the scheduler is run, and for the subsystem's default command to be scheduled. It
        is recommended to call this from the constructor of your subsystem implementations.

        :param subsystems: the subsystem to register
        """
        for subsystem in subsystems:
            if subsystem in self._subsystems:
                # DriverStation.reportWarning("Tried to register an already-registered subsystem", True)
                continue
            self._subsystems[subsystem] = None

    def unregisterSubsystem(self, *subsystems: Subsystem) -> None:
        """
        Un-registers subsystems with the scheduler. The subsystem will no longer have its periodic
        block called, and will not have its default command scheduled.

        :param subsystems: the subsystem to un-register
        """
        for subsystem in subsystems:
            self._subsystems.pop(subsystem)

    def setDefaultCommand(self, subsystem: Subsystem, defaultCommand: Command) -> None:
        """
        Sets the default command for a subsystem. Registers that subsystem if it is not already
        registered. Default commands will run whenever there is no other command currently scheduled
        that requires the subsystem. Default commands should be written to never end (i.e. their {@link
        Command#isFinished()} method should return false), as they would simply be re-scheduled if they
        do. Default commands must also require their subsystem.

        :param subsystem: the subsystem whose default command will be set
        :param defaultCommand: the default command to associate with the subsystem
        """
        self.requireNotComposed([defaultCommand])
        if subsystem not in defaultCommand.getRequirements():
            raise IllegalCommandUse("Default commands must require their subsystem!")
        if (
            defaultCommand.getInterruptionBehavior()
            != InterruptionBehavior.kCancelIncoming
        ):
            # DriverStation.reportWarning("Registering a non-interruptible default command\nThis will likely prevent any other commands from requiring this subsystem.", True)
            pass
        self._subsystems[subsystem] = defaultCommand

    def removeDefaultCommand(self, subsystem: Subsystem) -> None:
        """
        Removes the default command for a subsystem. The current default command will run until another
        command is scheduled that requires the subsystem, at which point the current default command
        will not be re-scheduled.

        :param subsystem: the subsystem whose default command will be removed
        """
        self._subsystems[subsystem] = None

    def getDefaultCommand(self, subsystem: Subsystem) -> Optional[Command]:
        """
        Gets the default command associated with this subsystem. Null if this subsystem has no default
        command associated with it.

        :param subsystem: the subsystem to inquire about
        :returns: the default command associated with the subsystem
        """
        return self._subsystems[subsystem]

    def cancel(self, *commands: Command) -> None:
        """
        Cancels commands. The scheduler will only call Command#end(boolean) method of the
        canceled command with {@code true}, indicating they were canceled (as opposed to finishing
        normally).

        Commands will be canceled regardless of InterruptionBehavior interruption behavior.

        :param commands: the commands to cancel
        """
        if self._inRunLoop:
            for command in commands:
                self._toCancel[command] = None
            return

        for command in commands:
            if not self.isScheduled(command):
                continue

            self._scheduledCommands.pop(command)
            for requirement in command.getRequirements():
                del self._requirements[requirement]
            command.end(True)
            for action in self._interruptActions:
                action(command)

    def cancelAll(self) -> None:
        """Cancels all commands that are currently scheduled."""
        self.cancel(*self._scheduledCommands)

    def isScheduled(self, *commands: Command) -> bool:
        """
        Whether the given commands are running. Note that this only works on commands that are directly
        scheduled by the scheduler; it will not work on commands inside compositions, as the scheduler
        does not see them.

        :param commands: the command to query
        :returns: whether the command is currently scheduled
        """
        return all(command in self._scheduledCommands for command in commands)

    def requiring(self, subsystem: Subsystem) -> Optional[Command]:
        """
        Returns the command currently requiring a given subsystem. None if no command is currently
        requiring the subsystem

        :param subsystem: the subsystem to be inquired about
        :returns: the command currently requiring the subsystem, or None if no command is currently
            scheduled
        """
        return self._requirements.get(subsystem)

    def disable(self) -> None:
        """Disables the command scheduler."""
        self._disabled = True

    def enable(self) -> None:
        """Enables the command scheduler."""
        self._disabled = False

    def onCommandInitialize(self, action: Callable[[Command], Any]) -> None:
        """
        Adds an action to perform on the initialization of any command by the scheduler.

        :param action: the action to perform
        """
        self._initActions.append(action)

    def onCommandExecute(self, action: Callable[[Command], Any]) -> None:
        """
        Adds an action to perform on the execution of any command by the scheduler.

        :param action: the action to perform
        """
        self._executeActions.append(action)

    def onCommandInterrupt(self, action: Callable[[Command], Any]) -> None:
        """
        Adds an action to perform on the interruption of any command by the scheduler.

        :param action: the action to perform
        """
        self._interruptActions.append(action)

    def onCommandFinish(self, action: Callable[[Command], Any]) -> None:
        """
        Adds an action to perform on the finishing of any command by the scheduler.

        :param action: the action to perform
        """
        self._finishActions.append(action)

    def registerComposedCommands(self, commands: Iterable[Command]) -> None:
        """
        Register commands as composed. An exception will be thrown if these commands are scheduled
        directly or added to a composition.

        :param commands: the commands to register
        @throws IllegalArgumentException if the given commands have already been composed.
        """
        self.requireNotComposed(commands)
        self._composedCommands.update(commands)

    def clearComposedCommands(self) -> None:
        """
        Clears the list of composed commands, allowing all commands to be freely used again.

        WARNING: Using this haphazardly can result in unexpected/undesirable behavior. Do not use
        this unless you fully understand what you are doing.
        """
        self._composedCommands.clear()

    def removeComposedCommands(self, commands: Iterable[Command]) -> None:
        """
        Removes a single command from the list of composed commands, allowing it to be freely used
        again.

        WARNING: Using this haphazardly can result in unexpected/undesirable behavior. Do not use
        this unless you fully understand what you are doing.

        :param command: the command to remove from the list of grouped commands
        """
        self._composedCommands.difference_update(commands)

    def requireNotComposed(self, commands: Iterable[Command]) -> None:
        """
        Requires that the specified command hasn't been already added to a composition.

        :param commands: The commands to check
        @throws IllegalArgumentException if the given commands have already been composed.
        """
        if not self._composedCommands.isdisjoint(commands):
            raise IllegalCommandUse(
                "Commands that have been composed may not be added to another composition or scheduled individually"
            )

    def isComposed(self, command: Command) -> bool:
        """
        Check if the given command has been composed.

        :param command: The command to check
        :returns: true if composed
        """
        return command in self.getComposedCommands()

    def getComposedCommands(self) -> Set[Command]:
        return self._composedCommands
