import pathlib
import sys

import pytest


def _make_robot_module(pytester):
    pytester.makepyfile(robot_module="""
import wpilib


class DummyRobot(wpilib.TimedRobot):
    def __init__(self):
        super().__init__()
        self.did_init = True


class AutonomousPeriodicFailed(wpilib.TimedRobot):
    def autonomous_periodic(self):
        assert False


class TeleopPeriodicFailed(wpilib.TimedRobot):
    def teleop_periodic(self):
        assert False


class TeleopInitFailed(wpilib.TimedRobot):
    def teleop_init(self):
        assert False


class IterativeStateRobot(wpilib.TimedRobot):

    def disabled_init(self):
        self.did_disabled_init = True

    def disabled_periodic(self):
        self.did_disabled_periodic = True

    def autonomous_init(self):
        self.did_auto_init = True

    def autonomous_periodic(self):
        self.did_auto_periodic = True

    def teleop_init(self):
        self.did_teleop_init = True

    def teleop_periodic(self):
        self.did_teleop_periodic = True

""")


def _configure_robot_testing_plugin(pytester, robot_class="DummyRobot"):
    pytester.makeconftest(f"""
import pathlib

from wpilib.testing.pytest_plugin import RobotTestingPlugin

from robot_module import {robot_class}


def pytest_configure(config):
    robot_file = pathlib.Path(__file__).resolve()
    config.pluginmanager.register(RobotTestingPlugin({robot_class}, robot_file, False))
""")


def _configure_isolated_plugin(
    pytester,
    parallelism=1,
    robot_class="DummyRobot",
    robot_module="robot_module",
    robot_file_name=None,
):
    if robot_file_name is None:
        robot_file = "pathlib.Path(__file__).resolve()"
    else:
        robot_file = f"pathlib.Path(__file__).parent / {robot_file_name!r}"

    pytester.makeconftest(f"""
import pathlib

from wpilib.testing.pytest_isolated_tests_plugin import IsolatedTestsPlugin

from {robot_module} import {robot_class}

def pytest_configure(config):
    if "--no-header" in config.invocation_params.args:
        return
    robot_file = {robot_file}
    config.pluginmanager.register(
        IsolatedTestsPlugin({robot_class}, robot_file, False, False, {parallelism})
    )
""")


def test_robot_testing_plugin_success(pytester):
    _make_robot_module(pytester)
    _configure_robot_testing_plugin(pytester)
    pytester.makepyfile(test_success="""
def test_robot_fixture(robot):
    assert robot.did_init
""")

    result = pytester.runpytest("-vv")

    result.assert_outcomes(passed=1)


def test_robot_testing_plugin_failure_shows_output(pytester):
    _make_robot_module(pytester)
    _configure_robot_testing_plugin(pytester)
    pytester.makepyfile(test_failure="""
def test_robot_failure(robot):
    print("checked failure output")
    assert False
""")

    result = pytester.runpytest("-vv")

    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(
        [
            "*test_failure.py::test_robot_failure FAILED*",
            "*checked failure output*",
        ]
    )


def test_isolated_plugin_process_and_output(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester)
    pytester.makepyfile(test_isolated="""
import os


def test_non_robot_pid():
    with open("non_robot_pid.txt", "w") as fp:
        fp.write(str(os.getpid()))


def test_robot_pid_one(robot):
    with open("robot_pid_one.txt", "w") as fp:
        fp.write(str(os.getpid()))


def test_robot_pid_two(robot):
    with open("robot_pid_two.txt", "w") as fp:
        fp.write(str(os.getpid()))


def test_robot_failure_output(robot):
    print("isolated failure output")
    assert False
""")

    result = pytester.runpytest_subprocess("-vv")

    result.assert_outcomes(passed=3, failed=1)
    result.stdout.fnmatch_lines(
        [
            "*test_isolated.py::test_robot_failure_output FAILED*",
            "*isolated failure output*",
        ]
    )

    root = pathlib.Path(pytester.path)
    main_pid = int(root.joinpath("non_robot_pid.txt").read_text())
    robot_pid_one = int(root.joinpath("robot_pid_one.txt").read_text())
    robot_pid_two = int(root.joinpath("robot_pid_two.txt").read_text())

    assert robot_pid_one != main_pid
    assert robot_pid_two != main_pid
    assert robot_pid_one != robot_pid_two


def test_isolated_plugin_uses_robot_directory_during_robot_import(pytester):
    robot_dir = pytester.path / "robot_project"
    robot_dir.mkdir()
    robot_dir.joinpath("__init__.py").touch()
    robot_dir.joinpath("robot.py").write_text("""
import wpilib

IMPORT_OPERATING_DIRECTORY = wpilib.get_operating_directory()


class ImportDirectoryRobot(wpilib.TimedRobot):
    pass
""")
    _configure_isolated_plugin(
        pytester,
        robot_class="ImportDirectoryRobot",
        robot_module="robot_project.robot",
        robot_file_name="robot_project/robot.py",
    )
    pytester.makepyfile(test_isolated="""
import pathlib

from robot_project.robot import IMPORT_OPERATING_DIRECTORY


def test_operating_directory(robot, robot_file):
    assert pathlib.Path(IMPORT_OPERATING_DIRECTORY) == robot_file.parent.absolute()
""")

    result = pytester.runpytest_subprocess("-vv")

    result.assert_outcomes(passed=1)


def test_isolated_plugin_assertion_rendering(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester)
    pytester.makepyfile(test_isolated="""
def test_robot_assertion_rendering(robot):
    assert "x" == "y"
""")

    result = pytester.runpytest_subprocess("-vv")

    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(
        [
            "*test_isolated.py::test_robot_assertion_rendering FAILED*",
            "*assert 'x' == 'y'*",
        ]
    )
    assert not any("_pytest/config/__init__.py" in line for line in result.outlines)


def test_isolated_plugin_no_duplicate_verbose_output(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester)
    pytester.makepyfile(test_isolated="""
def test_non_robot():
    assert True


def test_robot_one(robot):
    assert robot is not None


def test_robot_two(robot):
    assert robot is not None
""")

    result = pytester.runpytest_subprocess("-v")

    result.assert_outcomes(passed=3)
    assert (
        sum(1 for line in result.outlines if "test_isolated.py::test_robot_one" in line)
        == 1
    )
    assert (
        sum(1 for line in result.outlines if "test_isolated.py::test_robot_two" in line)
        == 1
    )


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="Process signal exits do not work on Windows",
)
def test_isolated_plugin_reports_signal_exit(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester)
    pytester.makepyfile(test_isolated="""
import os
import signal


def test_robot_signal_exit(robot):
    os.kill(os.getpid(), signal.SIGTERM)
""")

    result = pytester.runpytest_subprocess("-vv")

    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(
        [
            "*test_isolated.py::test_robot_signal_exit FAILED*",
            "*Terminated*",
        ]
    )


def test_isolated_plugin_shows_file_in_non_verbose_output(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester)
    pytester.makepyfile(test_isolated="""
def test_non_robot():
    assert True


def test_robot_one(robot):
    assert robot is not None


def test_robot_two(robot):
    assert robot is not None
""")

    result = pytester.runpytest_subprocess()

    result.assert_outcomes(passed=3)
    assert (
        sum(1 for line in result.outlines if line.startswith("test_isolated.py")) == 1
    )


def test_isolated_plugin_reports_worker_collection_exit(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester)
    with pytester.path.joinpath("conftest.py").open("a") as fp:
        fp.write("""


def pytest_collection_modifyitems(config, items):
    if "--no-header" in config.invocation_params.args:
        items.clear()
""")
    pytester.makepyfile(test_isolated="""
def test_robot(robot):
    assert robot is not None
""")

    result = pytester.runpytest_subprocess("-v")

    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*subprocess exited with exit code 5*"])


def test_isolated_plugin_maxfail_stops_early(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester)
    pytester.makepyfile(test_isolated="""
def test_robot_first(robot):
    assert False


def test_robot_second(robot):
    assert False
""")

    result = pytester.runpytest_subprocess("-v", "-x")

    result.assert_outcomes(failed=1)
    assert not any("test_robot_second" in line for line in result.outlines)


def test_isolated_plugin_maxfail_stops_deferred_tests(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=2)
    pytester.makepyfile(test_isolated="""
import pathlib
import time


def test_robot_failure(robot):
    assert False


def test_plain_waits_for_failure():
    time.sleep(1)


def test_plain_must_not_run():
    pathlib.Path("plain-ran").touch()
""")

    result = pytester.runpytest_subprocess("-v", "-x")

    assert result.parseoutcomes()["failed"] == 1
    assert result.ret == pytest.ExitCode.TESTS_FAILED
    assert not (pytester.path / "plain-ran").exists()


def test_isolated_plugin_runs_ordered_robot_tests_sequentially(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=2)
    pytester.makepyfile(test_ordered="""
import pathlib
import time

import pytest


@pytest.mark.order(2)
def test_second(robot):
    assert pathlib.Path("first-finished").exists()


@pytest.mark.order(1)
def test_first(robot):
    time.sleep(1)
    pathlib.Path("first-finished").touch()
""")

    result = pytester.runpytest_subprocess("-v")

    result.assert_outcomes(passed=2)


def test_isolated_plugin_finishes_ordered_robot_test_before_unordered_test(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=2)
    pytester.makepyfile(test_ordered="""
import pathlib
import time

import pytest


@pytest.mark.order("first")
def test_ordered(robot):
    time.sleep(1)
    pathlib.Path("ordered-finished").touch()


def test_unordered(robot):
    assert pathlib.Path("ordered-finished").exists()
""")

    result = pytester.runpytest_subprocess("-v")

    result.assert_outcomes(passed=2)


@pytest.mark.parametrize("isolated", [False, True])
def test_builtin_tests_module(pytester, isolated):
    _make_robot_module(pytester)
    if isolated:
        _configure_isolated_plugin(pytester, robot_class="DummyRobot")
    else:
        _configure_robot_testing_plugin(pytester, robot_class="DummyRobot")
    pytester.makepyfile(pyfrc_test="from wpilib.testing.robot_tests import *\n")

    result = pytester.runpytest_subprocess("-q")

    result.assert_outcomes(passed=4)


def _run_robot_suite(pytester, isolated, robot_class, test_source, *args):
    _make_robot_module(pytester)
    if isolated:
        _configure_isolated_plugin(pytester, robot_class=robot_class)
    else:
        _configure_robot_testing_plugin(pytester, robot_class=robot_class)
    pytester.makepyfile(test_robot=test_source)
    return pytester.runpytest_subprocess(*args)


_AUTO_FAILURES = [
    "AutonomousPeriodicFailed",
]

_TELEOP_FAILURES = [
    "TeleopPeriodicFailed",
    "TeleopInitFailed",
]


@pytest.mark.parametrize("isolated", [False, True])
@pytest.mark.parametrize("robot_class", _AUTO_FAILURES)
def test_autonomous_failure_detection(pytester, isolated, robot_class):
    result = _run_robot_suite(
        pytester,
        isolated,
        robot_class,
        """
def test_autonomous_failure(robot, control):
    with control.run_robot():
        control.step_timing(seconds=0.4, autonomous=True, enabled=True)
""",
        "-vv",
    )

    result.assert_outcomes(failed=1)


@pytest.mark.parametrize("isolated", [False, True])
@pytest.mark.parametrize("robot_class", _TELEOP_FAILURES)
def test_teleop_failure_detection(pytester, isolated, robot_class):
    result = _run_robot_suite(
        pytester,
        isolated,
        robot_class,
        """
def test_teleop_failure(robot, control):
    with control.run_robot():
        control.step_timing(seconds=0.4, autonomous=False, enabled=True)
""",
        "-vv",
    )

    result.assert_outcomes(failed=1)


@pytest.mark.parametrize("isolated", [False, True])
@pytest.mark.parametrize("robot_class", ["IterativeStateRobot"])
def test_robot_state_transitions(pytester, isolated, robot_class):
    expected = {
        "IterativeStateRobot": [
            "did_disabled_init",
            "did_disabled_periodic",
            "did_auto_init",
            "did_auto_periodic",
            "did_teleop_init",
            "did_teleop_periodic",
        ],
    }[robot_class]

    result = _run_robot_suite(
        pytester,
        isolated,
        robot_class,
        f"""
def test_state_transitions(robot, control):
    with control.run_robot():
        control.step_timing(seconds=0.4, autonomous=False, enabled=False)
        control.step_timing(seconds=0.4, autonomous=True, enabled=True)
        control.step_timing(seconds=0.4, autonomous=False, enabled=True)

        expected = {{name: True for name in {expected!r}}}
        attrs = {{name: getattr(robot, name, False) for name in {expected!r}}}
        assert expected == attrs
""",
        "-vv",
    )

    result.assert_outcomes(passed=1)


# Seconds a chain's sentinel writer sleeps before writing, when the test that reads that
# sentinel runs in an isolated subprocess.
#
# Why this is needed at all: a plain in-process test writes its sentinel within milliseconds,
# while a robot test needs a few hundred ms to spawn its subprocess and reach its first
# assertion. Without ordering support the robot test is merely *started* early, so by the time
# it actually looks, a fast writer has already written -- the case passes and proves nothing.
# Delaying the writer removes that race so the case fails without the fix, which is the only
# thing that makes it a guard.
#
# Choosing the value: sweeping the delay against the unfixed plugin put the cutoff between
# 150ms and 200ms on an M-series Mac (0/5 runs caught the bug at 150ms, 5/5 at 200ms). 1s
# leaves roughly 5x margin.
#
# The risk this carries: on a machine slow enough that a robot subprocess takes over a second
# to reach its assertion, these cases quietly stop catching regressions. They never fail
# wrongly -- with ordering support present they pass regardless of timing -- so the degradation
# is silent, which is the dangerous direction. If this suite starts running on much slower
# hardware, re-measure the cutoff rather than assuming this value still has margin.
ORDER_HANDOFF_DELAY = 1.0


def _handoff_sleep(reader_is_robot: bool) -> str:
    """Sleep line for a sentinel writer, or nothing when the reader is in-process."""
    return f"    time.sleep({ORDER_HANDOFF_DELAY})\n" if reader_is_robot else ""


@pytest.mark.parametrize("marker_style", ["numeric", "after", "before"])
@pytest.mark.parametrize(
    "first_type, middle_type, last_type",
    [
        ("ROBOT", "ROBOT", None),
        ("ROBOT", "PLAIN", None),
        ("PLAIN", "ROBOT", None),
        ("PLAIN", "PLAIN", None),
        ("ROBOT", "ROBOT", "PLAIN"),
        ("ROBOT", "PLAIN", "ROBOT"),
        ("PLAIN", "ROBOT", "ROBOT"),
        ("ROBOT", "PLAIN", "PLAIN"),
        ("PLAIN", "ROBOT", "PLAIN"),
        ("PLAIN", "PLAIN", "ROBOT"),
    ],
)
def test_order_marker_enforces_sequencing(
    pytester, first_type, middle_type, last_type, marker_style
):
    """
    Order markers enforce a first->middle->last chain across all mixed
    robot/non-robot permutations.

    test_first writes sentinel_1; test_middle reads sentinel_1 and writes
    sentinel_2; test_last reads sentinel_2.  The file lists them in reverse
    (last, middle, first) so collection order would fail -- passing proves the
    full chain was enforced.

    ROBOT = robot fixture (isolated subprocess)  PLAIN = plain test (in-process)

    numeric: first=order(1), middle=order(2), last=order(3)
    after:   middle=order(after="test_first"), last=order(after="test_middle")
    before:  first=order(before="test_middle"), middle=order(before="test_last")

    Not every permutation can detect a broken run loop, and that is expected:

    - PLAIN-PLAIN-None has no robot test at all, so there is nothing for the plugin to
      mis-order -- the old loop deferred non-robot tests but preserved their order among
      themselves. These three cases assert the chain still works; they are not regression
      guards and cannot be made into any.
    - Where the sentinel *reader* is a robot test, the writer sleeps ORDER_HANDOFF_DELAY so the
      reader cannot win the spawn race and pass by luck. See that constant for the measurement
      and the slow-machine caveat.
    """
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=4)

    # Only a robot reader needs the writer slowed down; a plain reader runs in-process and
    # already observes the violation directly.
    first_sleep = _handoff_sleep(middle_type == "ROBOT")
    middle_sleep = _handoff_sleep(last_type == "ROBOT")

    def params(t):
        return "(robot)" if t == "ROBOT" else "()"

    if marker_style == "numeric":
        first_mark = "@pytest.mark.order(1)\n"
        middle_mark = "@pytest.mark.order(2)\n"
        last_mark = "@pytest.mark.order(3)\n"
    elif marker_style == "before":
        first_mark = '@pytest.mark.order(before="test_middle")\n'
        middle_mark = '@pytest.mark.order(before="test_last")\n'
        last_mark = ""
    else:
        first_mark = ""
        middle_mark = '@pytest.mark.order(after="test_first")\n'
        last_mark = '@pytest.mark.order(after="test_middle")\n'

    pytester.makepyfile(
        test_order_sequence=(
            """\
import pathlib
import time

import pytest


"""
            + (
                f"""{last_mark}def test_last{params(last_type)}:
    assert pathlib.Path("sentinel_2.txt").exists(), "test_middle must run before test_last"


"""
                if last_type is not None
                else ""
            )
            + f"""{middle_mark}def test_middle{params(middle_type)}:
    assert pathlib.Path("sentinel_1.txt").exists(), "test_first must run before test_middle"
{middle_sleep}    pathlib.Path("sentinel_2.txt").write_text("done")


{first_mark}def test_first{params(first_type)}:
{first_sleep}    pathlib.Path("sentinel_1.txt").write_text("done")
"""
        )
    )

    result = pytester.runpytest_subprocess("-vv")
    count_of_tests = sum(x is not None for x in [first_type, middle_type, last_type])
    result.assert_outcomes(passed=count_of_tests)


@pytest.mark.parametrize(
    "ini_body, first_mark, second_mark",
    [
        (
            "addopts = --strict-markers",
            "@pytest.mark.order(1)",
            "@pytest.mark.order(2)",
        ),
        (
            "filterwarnings = error",
            "@pytest.mark.order(1)",
            "@pytest.mark.order(2)",
        ),
        (
            "filterwarnings = error",
            "",
            '@pytest.mark.order(after="test_first")',
        ),
    ],
    ids=["strict_markers", "warnings_as_errors", "relative_marker_stays_quiet"],
)
def test_order_marker_is_registered_in_isolated_subprocess(
    pytester, ini_body, first_mark, second_mark
):
    """
    Ordered robot tests must still run when the project treats unknown markers
    as a hard failure. The worker keeps pytest-order loaded for option parsing
    and test generation, but unregisters its collection-ordering plugin because
    a one-test worker cannot resolve relative markers. The marker must remain
    registered without emitting misleading relative-order warnings.
    """
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=2)
    pytester.makeini(f"[pytest]\n{ini_body}\n")

    pytester.makepyfile(test_strict_order=f"""\
import pathlib

import pytest


{second_mark}
def test_second(robot):
    assert pathlib.Path("strict_sentinel.txt").exists()


{first_mark}
def test_first(robot):
    pathlib.Path("strict_sentinel.txt").write_text("done")
""")

    result = pytester.runpytest_subprocess("-vv")
    result.assert_outcomes(passed=2, errors=0)
    assert not any("cannot execute" in line for line in result.outlines)


def test_order_options_are_available_in_isolated_subprocess(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester)
    pytester.makepyfile(test_ordered="""
import pytest


@pytest.mark.order(1)
def test_robot(robot):
    assert robot is not None
""")

    result = pytester.runpytest_subprocess("-v", "--order-scope=module")

    result.assert_outcomes(passed=1)


def test_multiple_order_markers_collect_in_isolated_subprocess(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester)
    pytester.makepyfile(test_ordered="""
import pytest


@pytest.mark.order(2)
@pytest.mark.order(1)
def test_robot(robot):
    assert robot is not None
""")

    result = pytester.runpytest_subprocess("-v")

    result.assert_outcomes(passed=2)


@pytest.mark.parametrize(
    "a_fixture, b_fixture",
    [("robot", "robot"), ("robot", ""), ("", "robot")],
    ids=["RR", "RN", "NR"],
)
def test_unordered_tests_still_run_in_parallel(pytester, a_fixture, b_fixture):
    """
    Tests WITHOUT @pytest.mark.order must not be serialised by order-marker
    support.  With parallelism=2, two 1.5 s tests must overlap in wall-clock
    time.

    NR is the case collection order alone cannot deliver: the plain test is
    collected first, so following the given order would run it to completion
    before the subprocess was even spawned.  Within a group the run loop is free
    to schedule for throughput, so it starts the isolated test before running any
    in-process test and the two overlap regardless of which was collected first.

    NN is omitted: two in-process tests both run here, and this process runs one
    test at a time -- serial by design, and no scheduling can change it.
    """
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=2)

    def params(f):
        return f"({f})" if f else "()"

    pytester.makepyfile(test_parallel_execution=f"""\
import pathlib
import time


def test_a{params(a_fixture)}:
    pathlib.Path("a_start.txt").write_text(str(time.monotonic()))
    time.sleep(1.5)
    pathlib.Path("a_end.txt").write_text(str(time.monotonic()))


def test_b{params(b_fixture)}:
    pathlib.Path("b_start.txt").write_text(str(time.monotonic()))
    time.sleep(1.5)
    pathlib.Path("b_end.txt").write_text(str(time.monotonic()))
""")

    result = pytester.runpytest_subprocess("-vv")
    result.assert_outcomes(passed=2)

    root = pathlib.Path(pytester.path)
    a_end = float((root / "a_end.txt").read_text())
    b_start = float((root / "b_start.txt").read_text())
    assert (
        b_start < a_end
    ), f"Expected parallel: b_start={b_start:.3f} a_end={a_end:.3f}"


def _read_times(pytester, *names):
    root = pathlib.Path(pytester.path)
    return {n: float((root / f"{n}.txt").read_text()) for n in names}


_TIMED_ROBOT_TEST = """\
def {name}(robot):
    pathlib.Path("{name}_start.txt").write_text(str(time.monotonic()))
    time.sleep(1.0)
    pathlib.Path("{name}_end.txt").write_text(str(time.monotonic()))
"""


def test_module_level_order_marker_parallel_within_group(pytester):
    """
    A module-level order marker positions the module as a whole; pytest-order
    explicitly does not constrain the order of the tests *inside* it ("the tests
    inside each module will be run in the same order as without any ordering").

    So the two modules must be serialised against each other, but the robot tests
    within a module must still overlap.  test_group_a is collected first but marked
    order(2), so passing also proves the modules were actually reordered.
    """
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=4)

    def module_src(order, names):
        return (
            "import pathlib\nimport time\nimport pytest\n\n"
            f"pytestmark = pytest.mark.order({order})\n\n\n"
            + "\n\n".join(_TIMED_ROBOT_TEST.format(name=n) for n in names)
        )

    pytester.makepyfile(
        test_group_a=module_src(2, ["test_a1", "test_a2"]),
        test_group_b=module_src(1, ["test_b1", "test_b2"]),
    )

    result = pytester.runpytest_subprocess("-vv")
    result.assert_outcomes(passed=4)

    t = _read_times(
        pytester,
        "test_a1_start",
        "test_a1_end",
        "test_a2_start",
        "test_a2_end",
        "test_b1_start",
        "test_b1_end",
        "test_b2_start",
        "test_b2_end",
    )

    # the order(1) module must fully complete before the order(2) module starts
    assert max(t["test_b1_end"], t["test_b2_end"]) <= min(
        t["test_a1_start"], t["test_a2_start"]
    ), f"module boundary not enforced: {t}"

    # ...but within each module the tests must have overlapped
    assert t["test_b2_start"] < t["test_b1_end"], f"module b serialised: {t}"
    assert t["test_a2_start"] < t["test_a1_end"], f"module a serialised: {t}"


def test_class_level_order_marker_parallel_within_group(pytester):
    """
    Same as the module-level case, for a class-level marker: "the class as a whole
    will be reordered without changing the test order inside the test class".
    TestAlpha is collected first but marked order(2).
    """
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=4)

    def class_src(cls, order, names):
        body = "\n".join(
            "    " + line if line else ""
            for n in names
            for line in _TIMED_ROBOT_TEST.format(name=n)
            .replace("(robot)", "(self, robot)")
            .split("\n")
        )
        return f"@pytest.mark.order({order})\nclass {cls}:\n{body}\n"

    pytester.makepyfile(
        test_classes="import pathlib\nimport time\nimport pytest\n\n\n"
        + class_src("TestAlpha", 2, ["test_x1", "test_x2"])
        + "\n"
        + class_src("TestBeta", 1, ["test_y1", "test_y2"])
    )

    result = pytester.runpytest_subprocess("-vv")
    result.assert_outcomes(passed=4)

    t = _read_times(
        pytester,
        "test_x1_start",
        "test_x1_end",
        "test_x2_start",
        "test_x2_end",
        "test_y1_start",
        "test_y1_end",
        "test_y2_start",
        "test_y2_end",
    )

    assert max(t["test_y1_end"], t["test_y2_end"]) <= min(
        t["test_x1_start"], t["test_x2_start"]
    ), f"class boundary not enforced: {t}"

    assert t["test_y2_start"] < t["test_y1_end"], f"TestBeta serialised: {t}"
    assert t["test_x2_start"] < t["test_x1_end"], f"TestAlpha serialised: {t}"


def test_separate_markers_with_equal_value_are_not_grouped(pytester):
    """
    Grouping is by marker *identity*, not equality.  Inheritance hands every test in
    a class/module the same Mark object, but two independent @pytest.mark.order(5)
    decorators are distinct objects that merely compare equal.  Those stay
    serialised -- the conservative choice, since only the inherited case has
    documented "order inside is unconstrained" semantics.
    """
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=4)

    pytester.makepyfile(
        test_equal_markers="import pathlib\nimport time\nimport pytest\n\n\n"
        + "@pytest.mark.order(5)\n"
        + _TIMED_ROBOT_TEST.format(name="test_p")
        + "\n\n@pytest.mark.order(5)\n"
        + _TIMED_ROBOT_TEST.format(name="test_q")
    )

    result = pytester.runpytest_subprocess("-vv")
    result.assert_outcomes(passed=2)

    t = _read_times(pytester, "test_p_end", "test_q_start")
    assert (
        t["test_p_end"] <= t["test_q_start"]
    ), f"equal-valued markers were merged into one group: {t}"


def test_robot_tests_ordered_relative_to_each_other(pytester):
    """
    Two robot-fixture tests carrying order markers must run one after the other.

    Both run in isolated subprocesses, so without order support they are started together
    and overlap. They are written to the file in reverse, so collection order alone fails.
    """
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=4)

    pytester.makepyfile(test_robot_chain=f"""\
import pathlib
import time

import pytest


@pytest.mark.order(2)
def test_robot_second(robot):
    assert pathlib.Path("robot_first.txt").exists(), "test_robot_first must run first"


@pytest.mark.order(1)
def test_robot_first(robot):
    time.sleep({ORDER_HANDOFF_DELAY})
    pathlib.Path("robot_first.txt").write_text("done")
""")

    result = pytester.runpytest_subprocess("-vv")
    result.assert_outcomes(passed=2)


def test_module_level_order_vs_robot_tests(pytester):
    """
    A module-level order marker must sequence a robot test against another module's tests.

    test_group_a is collected first but marked order(2), so passing also proves the modules
    were reordered. The robot test is the reader, since that is the direction the old run
    loop broke: robot tests were hoisted ahead of every non-robot test.
    """
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=4)

    pytester.makepyfile(
        test_group_a="""\
import pathlib

import pytest

pytestmark = pytest.mark.order(2)


def test_robot_reads(robot):
    assert pathlib.Path("early.txt").exists(), "the order(1) module must run first"
""",
        test_group_b=f"""\
import pathlib
import time

import pytest

pytestmark = pytest.mark.order(1)


def test_plain_writes():
    time.sleep({ORDER_HANDOFF_DELAY})
    pathlib.Path("early.txt").write_text("done")
""",
    )

    result = pytester.runpytest_subprocess("-vv")
    result.assert_outcomes(passed=2)


def test_class_level_order_vs_robot_tests(pytester):
    """
    A class-level order marker must sequence a robot test against another class's tests.

    TestLate is written first but marked order(2), so passing also proves the classes were
    reordered.
    """
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=4)

    pytester.makepyfile(test_class_chain=f"""\
import pathlib
import time

import pytest


@pytest.mark.order(2)
class TestLate:
    def test_robot_reads(self, robot):
        assert pathlib.Path("early.txt").exists(), "TestEarly must run first"


@pytest.mark.order(1)
class TestEarly:
    def test_plain_writes(self):
        time.sleep({ORDER_HANDOFF_DELAY})
        pathlib.Path("early.txt").write_text("done")
""")

    result = pytester.runpytest_subprocess("-vv")
    result.assert_outcomes(passed=2)


def test_class_level_relative_order_vs_robot_tests(pytester):
    """
    A class-level RELATIVE marker (`after=`) must sequence a robot test against another class.

    pytest-order documents referencing a test class by name from `before=`/`after=`, which is a
    different code path from the ordinal markers covered above.
    """
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=4)

    pytester.makepyfile(test_class_relative=f"""\
import pathlib
import time

import pytest


@pytest.mark.order(after="TestEarly")
class TestLate:
    def test_robot_reads(self, robot):
        assert pathlib.Path("early.txt").exists(), "TestEarly must run first"


class TestEarly:
    def test_plain_writes(self):
        time.sleep({ORDER_HANDOFF_DELAY})
        pathlib.Path("early.txt").write_text("done")
""")

    result = pytester.runpytest_subprocess("-vv")
    result.assert_outcomes(passed=2)


def test_module_level_relative_order_vs_robot_tests(pytester):
    """
    A module-level RELATIVE marker must sequence a robot test against another module's test.

    Note this form -- `pytestmark = pytest.mark.order(after="path::test")` -- is not documented
    upstream; pytest-order shows `before=`/`after=` only at function and class scope. It works
    because pytestmark is ordinary pytest marker inheritance, but it is de facto rather than
    de jure, so this test also serves to detect it changing.
    """
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=4)

    pytester.makepyfile(
        test_rel_a="""\
import pathlib

import pytest

pytestmark = pytest.mark.order(after="test_rel_b.py::test_plain_writes")


def test_robot_reads(robot):
    assert pathlib.Path("early.txt").exists(), "test_rel_b must run first"
""",
        test_rel_b=f"""\
import pathlib
import time


def test_plain_writes():
    time.sleep({ORDER_HANDOFF_DELAY})
    pathlib.Path("early.txt").write_text("done")
""",
    )

    result = pytester.runpytest_subprocess("-vv")
    result.assert_outcomes(passed=2)


def test_function_marker_inside_marked_class(pytester):
    """
    A function-level marker inside an already-marked class wins, and forms its own group.

    get_closest_marker returns the function's own Mark rather than the class's inherited one,
    so the marked method is a group of one: it is serialised against its own siblings, not
    merged with them. Here the method marked order(1) must overtake its class-mates even though
    the class as a whole is marked order(2).
    """
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester, parallelism=4)

    pytester.makepyfile(test_nested_marker=f"""\
import pathlib
import time

import pytest


@pytest.mark.order(2)
class TestGroup:
    def test_robot_reads(self, robot):
        assert pathlib.Path("early.txt").exists(), "the order(1) method must run first"

    @pytest.mark.order(1)
    def test_plain_writes_first(self):
        time.sleep({ORDER_HANDOFF_DELAY})
        pathlib.Path("early.txt").write_text("done")
""")

    result = pytester.runpytest_subprocess("-vv")
    result.assert_outcomes(passed=2)
