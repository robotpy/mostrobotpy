import commands2
from util import ConditionHolder


def test_select_command_int(scheduler: commands2.CommandScheduler):
    c = ConditionHolder()

    def _assert_false():
        assert False

    cmd1 = commands2.RunCommand(_assert_false)
    cmd2 = commands2.RunCommand(c.setTrue)
    cmd3 = commands2.RunCommand(_assert_false)

    sc = commands2.SelectCommand(lambda: 2, [(1, cmd1), (2, cmd2), (3, cmd3)])

    scheduler.schedule(sc)
    scheduler.run()

    assert c.cond


def test_select_command_str(scheduler: commands2.CommandScheduler):
    c = ConditionHolder()

    def _assert_false():
        assert False

    cmd1 = commands2.RunCommand(_assert_false)
    cmd2 = commands2.RunCommand(c.setTrue)
    cmd3 = commands2.RunCommand(_assert_false)

    sc = commands2.SelectCommand(lambda: "2", [("1", cmd1), ("2", cmd2), ("3", cmd3)])

    scheduler.schedule(sc)
    scheduler.run()

    assert c.cond
