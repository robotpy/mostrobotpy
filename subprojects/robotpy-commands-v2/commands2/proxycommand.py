from __future__ import annotations

from typing import Callable, overload

from .command import Command
from .commandgroup import *
from .util import format_args_kwargs


class ProxyCommand(Command):
    """
    Schedules the given command when this command is initialized, and ends when it ends. Useful for
    forking off from CommandGroups. If this command is interrupted, it will cancel the command.
    """

    _supplier: Callable[[], Command]

    @overload
    def __init__(self, supplier: Callable[[], Command]):
        """
        Creates a new ProxyCommand that schedules the supplied command when initialized, and ends when
        it is no longer scheduled. Useful for lazily creating commands at runtime.

        :param supplier: the command supplier"""
        ...

    @overload
    def __init__(self, command: Command):
        """
        Creates a new ProxyCommand that schedules the given command when initialized, and ends when it
        is no longer scheduled.

        :param command: the command to run by proxy"""
        ...

    def __init__(self, *args, **kwargs):
        super().__init__()

        def init_supplier(supplier: Callable[[], Command]):
            self._supplier = supplier

        def init_command(command: Command):
            self._supplier = lambda: command

        num_args = len(args) + len(kwargs)

        if num_args == 1 and len(kwargs) == 1:
            if "supplier" in kwargs:
                return init_supplier(kwargs["supplier"])
            elif "command" in kwargs:
                return init_command(kwargs["command"])
        elif num_args == 1 and len(args) == 1:
            if isinstance(args[0], Command):
                return init_command(args[0])
            elif callable(args[0]):
                return init_supplier(args[0])

        raise TypeError(
            f"""
TypeError: ProxyCommand(): incompatible function arguments. The following argument types are supported:
    1. (self: ProxyCommand, supplier: () -> Command)
    2. (self: ProxyCommand, command: Command)

Invoked with: {format_args_kwargs(self, *args, **kwargs)}
"""
        )

    def initialize(self):
        self._command = self._supplier()
        self._command.schedule()

    def end(self, interrupted: bool):
        if interrupted and self._command is not None:
            self._command.cancel()
        self._command = None

    def execute(self):
        pass

    def isFinished(self) -> bool:
        return self._command is None or not self._command.isScheduled()

    def runsWhenDisabled(self) -> bool:
        """
        Whether the given command should run when the robot is disabled. Override to return true if the
        command should run when disabled.

        :returns: true. Otherwise, this proxy would cancel commands that do run when disabled.
        """
        return True
