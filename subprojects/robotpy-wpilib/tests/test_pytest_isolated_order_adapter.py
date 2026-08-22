import pathlib
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from pytest_plugin_test_helpers import (
    _configure_isolated_plugin,
    _make_robot_module,
)


def _configure_recording_isolated_plugin(pytester):
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
    from wpilib.testing.pytest_isolated_order_adapter import PytestOrderAdapter

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

    config = SimpleNamespace(
        getoption=lambda name, default=None: default,
        pluginmanager=SimpleNamespace(get_plugin=lambda name: object()),
    )
    adapter = PytestOrderAdapter(config)
    groups = adapter.groups(ordered_items)

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
    from wpilib.testing.pytest_isolated_order_adapter import PytestOrderAdapter
    from wpilib.testing.pytest_isolated_tests_plugin import IsolatedTestsPlugin

    events = []
    session = _SchedulerSession(items, events)
    plugin = IsolatedTestsPlugin(object, pathlib.Path("robot.py"), False, False, 4)
    plugin._ordering = PytestOrderAdapter(session.config)

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


def test_order_marker_implies_dependency_boundaries(pytester):
    _make_robot_module(pytester)
    pytester.makeini(
        "[pytest]\nmarkers = dependency(*args, **kwargs): test dependency\n"
    )
    _configure_recording_isolated_plugin(pytester)
    pytester.makepyfile(test_dependency_order="""
import pathlib

import pytest


@pytest.mark.order(1)
class TestChain:
    @pytest.mark.dependency(depends=["prerequisite"])
    def test_isolated_dependent(self, robot):
        assert pathlib.Path("prerequisite-finished").exists()

    @pytest.mark.dependency(name="prerequisite")
    def test_plain_prerequisite(self):
        assert not pathlib.Path("isolated-started").exists()
        pathlib.Path("prerequisite-finished").touch()
""")

    result = pytester.runpytest_subprocess("-vv")

    result.assert_outcomes(passed=2)


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


def test_prefixed_order_markers_preserve_scheduler_boundaries(pytester):
    _make_robot_module(pytester)
    pytester.makeini(
        "[pytest]\n"
        "markers =\n"
        "    sequence1_setup: first test\n"
        "    sequence2_robot: second test\n"
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
    pytester.makepyfile(test_prefixed_order="""
import pathlib

import pytest


@pytest.mark.sequence2_robot
def test_isolated_dependent(robot):
    assert pathlib.Path("prerequisite-finished").exists()


@pytest.mark.sequence1_setup
def test_plain_prerequisite():
    assert not pathlib.Path("isolated-started").exists()
    pathlib.Path("prerequisite-finished").touch()
""")

    result = pytester.runpytest_subprocess("-vv", "--order-marker-prefix=sequence")

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
    "source,args",
    [
        (
            "@pytest.mark.sequence1\ndef test_robot(robot): pass",
            ("--order-marker-prefix=sequence",),
        ),
        (
            "@pytest.mark.dependency(name='x')\ndef test_robot(robot): pass",
            ("--order-dependencies",),
        ),
    ],
    ids=["prefix", "dependency"],
)
def test_nonstandard_ordering_requires_active_sorter(pytester, source, args):
    _make_robot_module(pytester)
    _configure_isolated_plugin(pytester)
    pytester.makeini(
        "[pytest]\nmarkers =\n"
        "    sequence1: first\n"
        "    dependency(*args, **kwargs): dependency\n"
    )
    pytester.makepyfile(test_ordered="import pytest\n\n" + source)

    result = pytester.runpytest_subprocess(
        "-p", "no:orderingplugin", *args
    )

    assert result.ret == pytest.ExitCode.USAGE_ERROR


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
