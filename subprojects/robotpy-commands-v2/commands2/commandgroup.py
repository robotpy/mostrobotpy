from __future__ import annotations

from .command import Command


class IllegalCommandUse(Exception):
    pass


class CommandGroup(Command):
    """
    A base for CommandGroups.
    """

    def addCommands(self, *commands: Command):
        """
        Adds the given commands to the command group.

        :param commands: The commands to add.
        """
        raise NotImplementedError
