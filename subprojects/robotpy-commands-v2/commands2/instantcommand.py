from __future__ import annotations

from typing import Callable, Optional

from .functionalcommand import FunctionalCommand
from .subsystem import Subsystem


class InstantCommand(FunctionalCommand):
    """
    A Command that runs instantly; it will initialize, execute once, and end on the same iteration of
    the scheduler. Users can either pass in a Runnable and a set of requirements, or else subclass
    this command if desired."""

    def __init__(
        self, toRun: Optional[Callable[[], None]] = None, *requirements: Subsystem
    ):
        """
        Creates a new InstantCommand that runs the given Runnable with the given requirements.

        :param toRun: the Runnable to run
        :param requirements: the subsystems required by this command"""
        super().__init__(
            toRun or (lambda: None),
            lambda: None,
            lambda _: None,
            lambda: True,
            *requirements,
        )
