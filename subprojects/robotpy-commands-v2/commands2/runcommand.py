from __future__ import annotations

from typing import Any, Callable

from .commandgroup import *
from .functionalcommand import FunctionalCommand
from .subsystem import Subsystem


class RunCommand(FunctionalCommand):
    """
    A command that runs a Runnable continuously. Has no end condition as-is; either subclass it or
    use Command#withTimeout(double) or Command#until(BooleanSupplier) to give it one.
    If you only wish to execute a Runnable once, use InstantCommand."""

    def __init__(self, toRun: Callable[[], Any], *requirements: Subsystem):
        """
        Creates a new RunCommand. The Runnable will be run continuously until the command ends. Does
        not run when disabled.

        :param toRun: the Runnable to run
        :param requirements: the subsystems to require"""
        super().__init__(
            lambda: None, toRun, lambda interrupted: None, lambda: False, *requirements
        )
