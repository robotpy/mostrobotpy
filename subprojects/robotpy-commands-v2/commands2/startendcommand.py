from __future__ import annotations

from typing import Any, Callable

from .commandgroup import *
from .functionalcommand import FunctionalCommand
from .subsystem import Subsystem


class StartEndCommand(FunctionalCommand):
    """
    A command that runs a given runnable when it is initialized, and another runnable when it ends.
    Useful for running and then stopping a motor, or extending and then retracting a solenoid. Has no
    end condition as-is; either subclass it or use Command#withTimeout(double) or {@link
    Command#until(java.util.function.BooleanSupplier)} to give it one.
    """

    def __init__(
        self,
        onInit: Callable[[], Any],
        onEnd: Callable[[], Any],
        *requirements: Subsystem,
    ):
        """
        Creates a new StartEndCommand. Will run the given runnables when the command starts and when it
        ends.

        :param onInit: the Runnable to run on command init
        :param onEnd: the Runnable to run on command end
        :param requirements: the subsystems required by this command"""
        super().__init__(
            onInit, lambda: None, lambda _: onEnd(), lambda: False, *requirements
        )
