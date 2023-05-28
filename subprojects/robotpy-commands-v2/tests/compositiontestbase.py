from typing import Generic, TypeVar

import commands2
import pytest

# T = TypeVar("T", bound=commands2.Command)
# T = commands2.Command

from util import *

if not IS_OLD_COMMANDS:

    class SingleCompositionTestBase:
        def composeSingle(self, member: commands2.Command):
            raise NotImplementedError

        @pytest.mark.parametrize(
            "interruptionBehavior",
            [
                commands2.InterruptionBehavior.kCancelSelf,
                commands2.InterruptionBehavior.kCancelIncoming,
            ],
        )
        def test_interruptible(
            self, interruptionBehavior: commands2.InterruptionBehavior
        ):
            command = self.composeSingle(
                commands2.WaitUntilCommand(lambda: False).withInterruptBehavior(
                    interruptionBehavior
                )
            )
            assert command.getInterruptionBehavior() == interruptionBehavior

        @pytest.mark.parametrize("runsWhenDisabled", [True, False])
        def test_runWhenDisabled(self, runsWhenDisabled: bool):
            command = self.composeSingle(
                commands2.WaitUntilCommand(lambda: False).ignoringDisable(
                    runsWhenDisabled
                )
            )
            assert command.runsWhenDisabled() == runsWhenDisabled

    class MultiCompositionTestBase(SingleCompositionTestBase):
        def compose(self, *members: commands2.Command):
            raise NotImplementedError

        def composeSingle(self, member: commands2.Command):
            return self.compose(member)

        @pytest.mark.parametrize(
            "expected,command1,command2,command3",
            [
                pytest.param(
                    commands2.InterruptionBehavior.kCancelSelf,
                    commands2.WaitUntilCommand(lambda: False).withInterruptBehavior(
                        commands2.InterruptionBehavior.kCancelSelf
                    ),
                    commands2.WaitUntilCommand(lambda: False).withInterruptBehavior(
                        commands2.InterruptionBehavior.kCancelSelf
                    ),
                    commands2.WaitUntilCommand(lambda: False).withInterruptBehavior(
                        commands2.InterruptionBehavior.kCancelSelf
                    ),
                    id="AllCancelSelf",
                ),
                pytest.param(
                    commands2.InterruptionBehavior.kCancelIncoming,
                    commands2.WaitUntilCommand(lambda: False).withInterruptBehavior(
                        commands2.InterruptionBehavior.kCancelIncoming
                    ),
                    commands2.WaitUntilCommand(lambda: False).withInterruptBehavior(
                        commands2.InterruptionBehavior.kCancelIncoming
                    ),
                    commands2.WaitUntilCommand(lambda: False).withInterruptBehavior(
                        commands2.InterruptionBehavior.kCancelIncoming
                    ),
                    id="AllCancelIncoming",
                ),
                pytest.param(
                    commands2.InterruptionBehavior.kCancelSelf,
                    commands2.WaitUntilCommand(lambda: False).withInterruptBehavior(
                        commands2.InterruptionBehavior.kCancelSelf
                    ),
                    commands2.WaitUntilCommand(lambda: False).withInterruptBehavior(
                        commands2.InterruptionBehavior.kCancelSelf
                    ),
                    commands2.WaitUntilCommand(lambda: False).withInterruptBehavior(
                        commands2.InterruptionBehavior.kCancelIncoming
                    ),
                    id="TwoCancelSelfOneIncoming",
                ),
                pytest.param(
                    commands2.InterruptionBehavior.kCancelSelf,
                    commands2.WaitUntilCommand(lambda: False).withInterruptBehavior(
                        commands2.InterruptionBehavior.kCancelIncoming
                    ),
                    commands2.WaitUntilCommand(lambda: False).withInterruptBehavior(
                        commands2.InterruptionBehavior.kCancelIncoming
                    ),
                    commands2.WaitUntilCommand(lambda: False).withInterruptBehavior(
                        commands2.InterruptionBehavior.kCancelSelf
                    ),
                    id="TwoCancelIncomingOneSelf",
                ),
            ],
        )
        def test_interruptible(self, expected, command1, command2, command3):
            command = self.compose(command1, command2, command3)
            assert command.getInterruptionBehavior() == expected

        @pytest.mark.parametrize(
            "expected,command1,command2,command3",
            [
                pytest.param(
                    False,
                    commands2.WaitUntilCommand(lambda: False).ignoringDisable(False),
                    commands2.WaitUntilCommand(lambda: False).ignoringDisable(False),
                    commands2.WaitUntilCommand(lambda: False).ignoringDisable(False),
                    id="AllFalse",
                ),
                pytest.param(
                    True,
                    commands2.WaitUntilCommand(lambda: False).ignoringDisable(True),
                    commands2.WaitUntilCommand(lambda: False).ignoringDisable(True),
                    commands2.WaitUntilCommand(lambda: False).ignoringDisable(True),
                    id="AllTrue",
                ),
                pytest.param(
                    False,
                    commands2.WaitUntilCommand(lambda: False).ignoringDisable(True),
                    commands2.WaitUntilCommand(lambda: False).ignoringDisable(True),
                    commands2.WaitUntilCommand(lambda: False).ignoringDisable(False),
                    id="TwoTrueOneFalse",
                ),
                pytest.param(
                    False,
                    commands2.WaitUntilCommand(lambda: False).ignoringDisable(False),
                    commands2.WaitUntilCommand(lambda: False).ignoringDisable(False),
                    commands2.WaitUntilCommand(lambda: False).ignoringDisable(True),
                    id="TwoFalseOneTrue",
                ),
            ],
        )
        def test_runWhenDisabled(self, expected, command1, command2, command3):
            command = self.compose(command1, command2, command3)
            assert command.runsWhenDisabled() == expected

else:

    class SingleCompositionTestBase:
        ...

    class MultiCompositionTestBase:
        ...
