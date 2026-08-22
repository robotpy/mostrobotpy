import pathlib
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

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


def test_isolated_plugin_worker_interruption_stops_session(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester)
    pytester.makepyfile(test_isolated="""
import pathlib
import pytest


@pytest.mark.order(1)
def test_robot_exit(robot):
    pytest.exit("worker requested exit")


@pytest.mark.order(2)
def test_later_group_must_not_run():
    pathlib.Path("later-group-ran").touch()
""")

    result = pytester.runpytest_subprocess("-v")

    assert result.ret == pytest.ExitCode.INTERRUPTED
    assert not (pytester.path / "later-group-ran").exists()


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


def test_plain_order_groups_preserve_shared_fixture_scopes(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester)
    pytester.makepyfile(
        test_plain="""
import pathlib

import pytest


EVENTS = pathlib.Path("fixture-events.txt")


def record(event):
    with EVENTS.open("a") as fp:
        fp.write(event + "\\n")


@pytest.fixture(scope="session")
def session_fixture():
    record("session setup")
    yield
    record("session teardown")


@pytest.fixture(scope="module")
def module_fixture():
    record("module setup")
    yield
    record("module teardown")


@pytest.fixture(scope="class")
def class_fixture():
    record("class setup")
    yield
    record("class teardown")


class TestPlain:
    @pytest.mark.order(1)
    def test_first(self, session_fixture, module_fixture, class_fixture):
        record("first")

    @pytest.mark.order(3)
    def test_second(self, session_fixture, module_fixture, class_fixture):
        record("second")
""",
        test_robot="""
import pytest


@pytest.mark.order(2)
def test_between_plain_groups(robot):
    pass
""",
    )

    result = pytester.runpytest_subprocess("-q")

    result.assert_outcomes(passed=3)
    assert (pytester.path / "fixture-events.txt").read_text().splitlines() == [
        "session setup",
        "module setup",
        "class setup",
        "first",
        "second",
        "class teardown",
        "module teardown",
        "session teardown",
    ]


def test_order_marker_groups_use_real_pytest_marker_inheritance(pytester):
    from wpilib.testing.pytest_isolated_tests_plugin import _order_marker_groups

    items = pytester.getitems("""
import pytest


@pytest.mark.order(1)
class TestInherited:
    def test_inherited_one(self):
        pass

    def test_inherited_two(self):
        pass


@pytest.mark.order(1)
def test_independent_one():
    pass


@pytest.mark.order(1)
def test_independent_two():
    pass


@pytest.mark.order(1)
class TestOverride:
    def test_class_marker(self):
        pass

    @pytest.mark.order(2)
    def test_function_override(self):
        pass
""")
    items_by_name = {item.name: item for item in items}
    ordered_items = [
        items_by_name[name]
        for name in (
            "test_inherited_one",
            "test_inherited_two",
            "test_independent_one",
            "test_independent_two",
            "test_class_marker",
            "test_function_override",
        )
    ]

    groups = _order_marker_groups(ordered_items)

    assert [[item.name for item in group] for group in groups] == [
        ["test_inherited_one", "test_inherited_two"],
        ["test_independent_one"],
        ["test_independent_two"],
        ["test_class_marker"],
        ["test_function_override"],
    ]
    assert items_by_name["test_class_marker"].get_closest_marker("order").args == (1,)
    assert items_by_name["test_function_override"].get_closest_marker("order").args == (
        2,
    )


class _SchedulerHook:
    def __init__(self, events):
        self.events = events

    def pytest_runtest_protocol(self, item, nextitem):
        self.events.append(("plain", item.name))


class _SchedulerSession:
    Interrupted = pytest.Session.Interrupted
    Failed = pytest.Session.Failed

    def __init__(self, items, events):
        self.items = items
        self.testsfailed = 0
        self.shouldfail = False
        self.shouldstop = False
        self.config = SimpleNamespace(
            option=SimpleNamespace(
                continue_on_collection_errors=False,
                collectonly=False,
            ),
            hook=_SchedulerHook(events),
            getoption=lambda name, default=None: default,
        )


def _scheduler_item(name, marker, uses_robot):
    item = MagicMock(spec=pytest.Function)
    item.name = name
    item.fixturenames = ["robot"] if uses_robot else []
    item.get_closest_marker.return_value = marker
    return item


def _scheduler_events(monkeypatch, items):
    from wpilib.testing.pytest_isolated_tests_plugin import IsolatedTestsPlugin

    events = []
    session = _SchedulerSession(items, events)
    plugin = IsolatedTestsPlugin(object, pathlib.Path("robot.py"), False, False, 4)

    def start(item):
        events.append(("start", item.name))
        conn = SimpleNamespace(poll=lambda: False)
        return SimpleNamespace(item=item, conn=conn)

    def wait(running, session):
        events.extend(("finish", job.item.name) for job in running)
        running.clear()

    monkeypatch.setattr(plugin, "_start_isolated_test", start)
    monkeypatch.setattr(plugin, "_wait_for_jobs", wait)

    assert plugin.pytest_runtestloop(session) is True
    return events


_ORDERED_TYPE_CHAINS = [
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
]


@pytest.mark.parametrize("marker_style", ["numeric", "after", "before"])
@pytest.mark.parametrize("test_types", _ORDERED_TYPE_CHAINS)
def test_order_groups_do_not_cross_scheduler_boundaries(
    monkeypatch, marker_style, test_types
):
    # pytest-order has already sorted these items. The three patterns model
    # which tests carry markers for ordinal, after=, and before= ordering.
    first_marker = object()
    middle_marker = object()
    last_marker = object()
    markers = {
        "numeric": (first_marker, middle_marker, last_marker),
        "after": (None, middle_marker, last_marker),
        "before": (first_marker, middle_marker, None),
    }[marker_style]

    items = []
    expected = []
    for name, test_type, marker in zip(
        ("first", "middle", "last"), test_types, markers
    ):
        if test_type is None:
            continue

        uses_robot = test_type == "ROBOT"
        items.append(_scheduler_item(name, marker, uses_robot))
        if uses_robot:
            expected.extend((("start", name), ("finish", name)))
        else:
            expected.append(("plain", name))

    assert _scheduler_events(monkeypatch, items) == expected


def test_dependency_ordering_does_not_cross_scheduler_boundaries(pytester):
    _make_robot_module(pytester)
    pytester.makeini(
        "[pytest]\nmarkers = dependency(*args, **kwargs): test dependency\n"
    )
    pytester.makeconftest("""
import pathlib

from wpilib.testing.pytest_isolated_tests_plugin import IsolatedTestsPlugin

from robot_module import DummyRobot


class RecordingIsolatedTestsPlugin(IsolatedTestsPlugin):
    def _start_isolated_test(self, item):
        pathlib.Path("isolated-started").touch()
        return super()._start_isolated_test(item)


def pytest_configure(config):
    if "--no-header" in config.invocation_params.args:
        return
    config.pluginmanager.register(
        RecordingIsolatedTestsPlugin(
            DummyRobot, pathlib.Path(__file__).resolve(), False, False, 2
        )
    )
""")
    pytester.makepyfile(test_dependency_order="""
import pathlib

import pytest


@pytest.mark.dependency(depends=["prerequisite"])
def test_isolated_dependent(robot):
    assert pathlib.Path("prerequisite-finished").exists()


@pytest.mark.dependency(name="prerequisite")
def test_plain_prerequisite():
    assert not pathlib.Path("isolated-started").exists()
    pathlib.Path("prerequisite-finished").touch()
""")

    result = pytester.runpytest_subprocess("-vv", "--order-dependencies")

    result.assert_outcomes(passed=2)


def test_inherited_order_marker_group_runs_in_parallel(monkeypatch):
    inherited_marker = object()
    next_marker = object()
    items = [
        _scheduler_item("plain", inherited_marker, False),
        _scheduler_item("robot_one", inherited_marker, True),
        _scheduler_item("robot_two", inherited_marker, True),
        _scheduler_item("next_robot", next_marker, True),
    ]

    assert _scheduler_events(monkeypatch, items) == [
        ("start", "robot_one"),
        ("start", "robot_two"),
        ("plain", "plain"),
        ("finish", "robot_one"),
        ("finish", "robot_two"),
        ("start", "next_robot"),
        ("finish", "next_robot"),
    ]


class _EqualMarker:
    def __eq__(self, other):
        return isinstance(other, _EqualMarker)


def test_equal_but_distinct_order_markers_form_boundaries(monkeypatch):
    first_marker = _EqualMarker()
    second_marker = _EqualMarker()
    items = [
        _scheduler_item("first", first_marker, True),
        _scheduler_item("second", second_marker, True),
    ]

    assert _scheduler_events(monkeypatch, items) == [
        ("start", "first"),
        ("finish", "first"),
        ("start", "second"),
        ("finish", "second"),
    ]


@pytest.mark.parametrize(
    "disabled_plugin", ["pytest_order", "orderingplugin"], ids=["absent", "disabled"]
)
def test_order_marker_requires_pytest_order(pytester, disabled_plugin):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester)
    pytester.makepyfile(test_ordered="""
import pytest


@pytest.mark.order(2)
def test_second(robot):
    pass


@pytest.mark.order(1)
def test_first(robot):
    pass
""")

    result = pytester.runpytest_subprocess("-p", f"no:{disabled_plugin}")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*pytest-order is required to use order markers*"])


def test_pytest_order_is_optional_without_order_markers(pytester):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester)
    pytester.makepyfile(test_unordered="""
def test_robot(robot):
    pass
""")

    result = pytester.runpytest_subprocess("-p", "no:pytest_order")

    result.assert_outcomes(passed=1)


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
