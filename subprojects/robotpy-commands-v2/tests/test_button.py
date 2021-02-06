import commands2
import commands2.button

from util import Counter


class MyButton(commands2.button.Button):
    def __init__(self):
        super().__init__(self.isPressed)
        self.pressed = False

    def isPressed(self) -> bool:
        return self.pressed

    def setPressed(self, value: bool):
        self.pressed = value


class MyCommand(commands2.CommandBase):
    executed = 0

    ended = 0
    canceled = 0

    def execute(self) -> None:
        self.executed += 1

    def end(self, interrupted: bool) -> None:
        self.ended += 1
        if interrupted:
            self.canceled += 1


def test_when_pressed(scheduler: commands2.CommandScheduler):
    cmd1 = MyCommand()
    button = MyButton()
    button.setPressed(False)

    button.whenPressed(cmd1)
    scheduler.run()

    assert not cmd1.executed
    assert not scheduler.isScheduled(cmd1)

    button.setPressed(True)
    scheduler.run()
    scheduler.run()

    assert cmd1.executed
    assert scheduler.isScheduled(cmd1)


def test_when_released(scheduler: commands2.CommandScheduler):
    cmd1 = MyCommand()
    button = MyButton()
    button.setPressed(True)

    button.whenReleased(cmd1)
    scheduler.run()

    assert not cmd1.executed
    assert not scheduler.isScheduled(cmd1)

    button.setPressed(False)
    scheduler.run()
    scheduler.run()

    assert cmd1.executed
    assert scheduler.isScheduled(cmd1)


def test_while_held(scheduler: commands2.CommandScheduler):
    cmd1 = MyCommand()
    button = MyButton()
    button.setPressed(False)

    button.whileHeld(cmd1)
    scheduler.run()

    assert not cmd1.executed
    assert not scheduler.isScheduled(cmd1)

    button.setPressed(True)
    scheduler.run()
    scheduler.run()

    assert cmd1.executed == 2
    assert scheduler.isScheduled(cmd1)

    button.setPressed(False)
    scheduler.run()

    assert cmd1.executed == 2
    assert not scheduler.isScheduled(cmd1)


def test_when_held(scheduler: commands2.CommandScheduler):
    cmd1 = MyCommand()
    button = MyButton()
    button.setPressed(False)

    button.whenHeld(cmd1)
    scheduler.run()

    assert not cmd1.executed
    assert not scheduler.isScheduled(cmd1)

    button.setPressed(True)
    scheduler.run()
    scheduler.run()

    assert cmd1.executed == 2
    assert scheduler.isScheduled(cmd1)

    button.setPressed(False)
    scheduler.run()

    assert cmd1.executed == 2
    assert not scheduler.isScheduled(cmd1)


def test_toggle_when_pressed(scheduler: commands2.CommandScheduler):
    cmd1 = MyCommand()
    button = MyButton()
    button.setPressed(False)

    button.toggleWhenPressed(cmd1)
    scheduler.run()

    assert not cmd1.executed
    assert not scheduler.isScheduled(cmd1)

    button.setPressed(True)
    scheduler.run()

    assert cmd1.executed
    assert scheduler.isScheduled(cmd1)


def test_cancel_when_pressed(scheduler: commands2.CommandScheduler):
    cmd1 = MyCommand()
    button = MyButton()
    button.setPressed(False)

    scheduler.schedule(cmd1)

    button.cancelWhenPressed(cmd1)
    scheduler.run()

    assert cmd1.executed == 1
    assert cmd1.ended == 0
    assert cmd1.canceled == 0
    assert scheduler.isScheduled(cmd1)

    button.setPressed(True)
    scheduler.run()
    scheduler.run()

    assert cmd1.executed == 1
    assert cmd1.ended == 1
    assert cmd1.canceled == 1
    assert not scheduler.isScheduled(cmd1)


def test_function_bindings(scheduler: commands2.CommandScheduler):

    buttonWhenPressed = MyButton()
    buttonWhileHeld = MyButton()
    buttonWhenReleased = MyButton()

    buttonWhenPressed.setPressed(False)
    buttonWhileHeld.setPressed(True)
    buttonWhenReleased.setPressed(True)

    counter = Counter()

    buttonWhenPressed.whenPressed(counter.increment)
    buttonWhileHeld.whileHeld(counter.increment)
    buttonWhenReleased.whenReleased(counter.increment)

    scheduler.run()
    buttonWhenPressed.setPressed(True)
    buttonWhenReleased.setPressed(False)
    scheduler.run()

    assert counter.value == 4


def test_button_composition(scheduler: commands2.CommandScheduler):

    button1 = MyButton()
    button2 = MyButton()

    button1.setPressed(True)
    button2.setPressed(False)

    # TODO: not sure if this is a great idea?
    assert button1
    assert not button2

    assert not button1.and_(button2)
    assert button1.or_(button2)
    assert not button1.not_()
    assert button1.and_(button2.not_())
