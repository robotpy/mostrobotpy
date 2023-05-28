from __future__ import annotations

from typing import Any, Callable

from wpilib import Notifier

from .command import Command
from .commandgroup import *
from .subsystem import Subsystem


class NotifierCommand(Command):
    """
    A command that starts a notifier to run the given runnable periodically in a separate thread. Has
    no end condition as-is; either subclass it or use Command#withTimeout(double) or {@link
    Command#until(java.util.function.BooleanSupplier)} to give it one.

    WARNING: Do not use this class unless you are confident in your ability to make the executed
    code thread-safe. If you do not know what "thread-safe" means, that is a good sign that you
    should not use this class."""

    def __init__(
        self, toRun: Callable[[], Any], period: float, *requirements: Subsystem
    ):
        """
        Creates a new NotifierCommand.

        :param toRun: the runnable for the notifier to run
        :param period: the period at which the notifier should run, in seconds
        :param requirements: the subsystems required by this command"""
        super().__init__()

        self.notifier = Notifier(toRun)
        self.period = period
        self.addRequirements(*requirements)

    def initialize(self):
        self.notifier.startPeriodic(self.period)

    def end(self, interrupted: bool):
        self.notifier.stop()
