from .button import Trigger
from .command import Command, InterruptionBehavior

from . import cmd

# from .cmd import (
#     deadline,
#     either,
#     none,
#     parallel,
#     print_,
#     race,
#     repeatingSequence,
#     run,
#     runEnd,
#     runOnce,
#     select,
#     sequence,
#     startEnd,
#     waitSeconds,
#     waitUntil,
# )
from .commandgroup import CommandGroup, IllegalCommandUse
from .commandscheduler import CommandScheduler
from .conditionalcommand import ConditionalCommand
from .functionalcommand import FunctionalCommand
from .instantcommand import InstantCommand
from .notifiercommand import NotifierCommand
from .parallelcommandgroup import ParallelCommandGroup
from .paralleldeadlinegroup import ParallelDeadlineGroup
from .parallelracegroup import ParallelRaceGroup
from .perpetualcommand import PerpetualCommand
from .pidcommand import PIDCommand
from .pidsubsystem import PIDSubsystem
from .printcommand import PrintCommand
from .proxycommand import ProxyCommand
from .proxyschedulecommand import ProxyScheduleCommand
from .repeatcommand import RepeatCommand
from .runcommand import RunCommand
from .schedulecommand import ScheduleCommand
from .selectcommand import SelectCommand
from .sequentialcommandgroup import SequentialCommandGroup
from .startendcommand import StartEndCommand
from .subsystem import Subsystem
from .timedcommandrobot import TimedCommandRobot
from .trapezoidprofilesubsystem import TrapezoidProfileSubsystem
from .waitcommand import WaitCommand
from .waituntilcommand import WaitUntilCommand
from .wrappercommand import WrapperCommand

__all__ = [
    "cmd",
    "Command",
    "CommandGroup",
    "CommandScheduler",
    "ConditionalCommand",
    "FunctionalCommand",
    "IllegalCommandUse",
    "InstantCommand",
    "InterruptionBehavior",
    "NotifierCommand",
    "ParallelCommandGroup",
    "ParallelDeadlineGroup",
    "ParallelRaceGroup",
    "PerpetualCommand",
    "PIDCommand",
    "PIDSubsystem",
    "PrintCommand",
    "ProxyCommand",
    "ProxyScheduleCommand",
    "RepeatCommand",
    "RunCommand",
    "ScheduleCommand",
    "SelectCommand",
    "SequentialCommandGroup",
    "StartEndCommand",
    "Subsystem",
    "TimedCommandRobot",
    "TrapezoidProfileSubsystem",
    "WaitCommand",
    "WaitUntilCommand",
    "WrapperCommand",
    # "none",
    # "runOnce",
    # "run",
    # "startEnd",
    # "runEnd",
    # "print_",
    # "waitSeconds",
    # "waitUntil",
    # "either",
    # "select",
    # "sequence",
    # "repeatingSequence",
    # "parallel",
    # "race",
    # "deadline",
    "Trigger",  # was here in 2023
]


def __getattr__(attr):
    if attr == "SubsystemBase":
        import warnings

        warnings.warn("SubsystemBase is deprecated", DeprecationWarning, stacklevel=2)
        return Subsystem

    if attr == "CommandBase":
        import warnings

        warnings.warn("CommandBase is deprecated", DeprecationWarning, stacklevel=2)
        return Command

    raise AttributeError("module {!r} has no attribute " "{!r}".format(__name__, attr))
