import dataclasses
import logging
import multiprocessing
import multiprocessing.connection
import os
import pathlib
import pickle
import signal
import sys
import time
import typing as T

from collections import deque

import pytest

import robotpy.main
import wpilib


from .pytest_plugin import RobotTestingPlugin


class _NullTerminalWriter:
    def _highlight(self, source, lexer="python"):
        return source


class _NullTerminalReporter:
    """Minimal terminal reporter used in worker processes."""

    def __init__(self):
        self._tw = _NullTerminalWriter()

    def write(self, *args, **kwargs):
        pass

    def line(self, *args, **kwargs):
        pass


def _enable_faulthandler():
    #
    # In the event of a segfault, faulthandler will dump the currently
    # active stack so you can figure out what went wrong.
    #
    # Additionally, on non-Windows platforms we register a SIGUSR2
    # handler -- if you send the robot process a SIGUSR2, then
    # faulthandler will dump all of your current stacks. This can
    # be really useful for figuring out things like deadlocks.
    #

    import logging

    logger = logging.getLogger("faulthandler")

    try:
        # These should work on all platforms
        import faulthandler

        faulthandler.enable()
    except Exception as e:
        logger.warning("Could not enable faulthandler: %s", e)
        return

    try:
        faulthandler.register(signal.SIGUSR2)
        logger.info("registered SIGUSR2 for PID %s", os.getpid())
    except Exception:
        return


class WorkerPlugin:
    """
    This pytest plugin runs in the isolated process that runs a test that uses the
    robot fixture.

    Heavily borrowed from pytest-xdist WorkerInteractor
    """

    def __init__(self, channel: multiprocessing.connection.Connection):
        self.channel = channel

    def sendevent(self, name: str, **kwargs: object):
        self.channel.send((name, kwargs))

    @pytest.hookimpl
    def pytest_configure(self, config: pytest.Config):
        # The worker runs with "-p", "no:order" (see _run_test), which unloads
        # pytest-order entirely -- including its registration of the "order"
        # marker. The @pytest.mark.order decorators are still on the tests we
        # collect here, so without re-registering the marker they are "unknown"
        # to this process: --strict-markers turns that into a collection error,
        # and filterwarnings=error promotes the PytestUnknownMarkWarning into
        # one. Both settings reach the worker, because it inherits the parent's
        # command line and chdirs to the project root before reading the ini.
        #
        # Registering the marker restores those configurations without
        # reactivating the reordering we deliberately turned off.
        config.addinivalue_line(
            "markers",
            "order(*args, **kwargs): ordering is resolved by the parent process",
        )

    @pytest.hookimpl(wrapper=True)
    def pytest_sessionstart(self, session: pytest.Session):
        self.config = session.config

        # When we disable terminalreporter in worker mode we still need a
        # minimal reporter so assertion introspection can render diffs.
        if self.config.pluginmanager.get_plugin("terminalreporter") is None:
            self.config.pluginmanager.unblock("terminalreporter")
            self.config.pluginmanager.register(
                _NullTerminalReporter(), "terminalreporter"
            )

        return (yield)

    @pytest.hookimpl
    def pytest_internalerror(self, excrepr: object):
        formatted_error = str(excrepr)
        for line in formatted_error.split("\n"):
            print("IERROR>", line, file=sys.stderr)
        self.sendevent("internal_error", formatted_error=formatted_error)

    @pytest.hookimpl
    def pytest_runtest_logstart(
        self,
        nodeid: str,
        location: tuple[str, int | None, str],
    ):
        self.sendevent("logstart", nodeid=nodeid, location=location)

    @pytest.hookimpl
    def pytest_runtest_logfinish(
        self,
        nodeid: str,
        location: tuple[str, int | None, str],
    ):
        self.sendevent("logfinish", nodeid=nodeid, location=location)

    @pytest.hookimpl
    def pytest_runtest_logreport(self, report: pytest.TestReport):
        data = self.config.hook.pytest_report_to_serializable(
            config=self.config, report=report
        )
        self.sendevent("testreport", data=data)


def _run_test(
    item_nodeid, config_args, robot_class_data, robot_file, verbose, pipe, root_path
):
    """This function runs in a subprocess"""
    logging.root.addHandler(logging.NullHandler())
    logging.root.setLevel(logging.DEBUG if verbose else logging.INFO)

    _enable_faulthandler()

    # This is used by the operating and deploy directory lookups, so set it
    # before importing the robot module.
    robotpy.main.robot_py_path = robot_file
    robot_class = pickle.loads(robot_class_data)

    os.chdir(root_path)

    # keep the plugins around because it has a reference to the robot
    # and we don't want it to die and deadlock
    plugin = RobotTestingPlugin(robot_class, robot_file, True)
    worker_plugin = WorkerPlugin(pipe)

    ec = pytest.main(
        [
            item_nodeid,
            "--no-header",
            "-p",
            "no:terminalreporter",
            # "-p", "no:order" tells pytest in the isolated subprocess to not run pytest-order or look at
            # the @pytest.mark.order decorators. This is fine because the isolated subprocess runs just one
            # test at a time, so order does not matter at this level. The purpose of not running
            # pytest-order is so that it doesn't give misleading warnings like:
            #   WARNING: cannot execute 'test_step2_reads_sentinel' relative to others:
            #   'test_step1_writes_sentinel' - ignoring the marker.
            # The warning would be accurate from the isolated subprocess point of view,
            # it can't see the other test, but it is misleading because the main process
            # successfully ordered the tests.
            #
            # Unloading the plugin also drops its registration of the "order" marker, so
            # WorkerPlugin.pytest_configure re-registers it.
            "-p",
            "no:order",
            *config_args,
        ],
        plugins=[plugin, worker_plugin],
    )

    # ensure output is printed out
    sys.stdout.flush()

    # Don't let the process die, let the parent kill us to avoid
    # python interpreter badness
    worker_plugin.sendevent("finished", exit_code=ec)
    pipe.close()

    # ensure that the gc doesn't collect the plugin..
    while plugin:
        time.sleep(100)


@dataclasses.dataclass
class IsolatedTestJob:
    item: pytest.Function
    conn: multiprocessing.connection.Connection
    process: multiprocessing.Process
    start_time: float
    exit_code: int | None = None

    finished: bool = False

    # set when the worker indicates it has finished
    worker_completed: bool = False

    def set_exit_code(self, ec: int):
        if self.exit_code is None:
            self.exit_code = ec


def _order_marker_groups(
    items: list[pytest.Item],
) -> T.Iterator[list[pytest.Function]]:
    """
    Split collected items into consecutive runs that share one order marker.

    An order marker applied to a class or module is inherited by every test underneath it,
    and get_closest_marker returns the *same* Mark object for each of them. Grouping by
    identity therefore treats those tests as one group: the group is serialized against
    everything outside it, while its members -- whose relative order pytest-order explicitly
    does not constrain -- can be scheduled freely. Identity is required rather than ==,
    because two independent @pytest.mark.order(5) decorators compare equal but are separate
    constraints that must not be merged into one group.

    Unmarked tests all return None, so a run of them forms a single group.
    """
    group: list[pytest.Function] = []
    prev_marker = None

    for item in items:
        assert isinstance(item, pytest.Function)

        marker = item.get_closest_marker("order")
        if group and marker is not prev_marker:
            yield group
            group = []

        group.append(item)
        prev_marker = marker

    if group:
        yield group


class IsolatedTestsPlugin:
    """
    This pytest plugin runs any test that uses the 'robot' fixture in an
    isolated subprocess
    """

    def __init__(
        self,
        robot_class: T.Type[wpilib.RobotBase],
        robot_file: pathlib.Path,
        builtin_tests: bool,
        verbose: bool,
        parallelism: int,
    ):
        self._robot_class = robot_class
        self._robot_file = robot_file
        self._builtin_tests = builtin_tests
        self._verbose = verbose

        if parallelism < 1:
            try:
                parallelism = multiprocessing.cpu_count() - 1
            except NotImplementedError:
                parallelism = 1

        self._parallelism = max(1, parallelism)
        self._shouldstop = False

    @pytest.hookimpl(wrapper=True)
    def pytest_sessionstart(self, session: pytest.Session):
        self._config = session.config
        self._maxfail: int = self._config.getvalue("maxfail")
        self._countfailures = 0
        self._shouldstop = False

        multiprocessing.set_start_method("spawn")

        return (yield)

    @pytest.hookimpl
    def pytest_runtestloop(self, session: pytest.Session) -> bool:
        if (
            session.testsfailed
            and not session.config.option.continue_on_collection_errors
        ):
            raise session.Interrupted(
                f"{session.testsfailed} error{'s' if session.testsfailed != 1 else ''} during collection"
            )

        if session.config.option.collectonly:
            return True

        running: list[IsolatedTestJob] = []
        try:
            # Run tests one order marker group at a time, preserving the boundaries between
            # groups while scheduling freely inside them.
            #
            # pytest-order has already sorted session.items during collection, so all this has
            # to do is stop tests from overtaking each other across an ordering boundary.
            #
            # Within a group pytest-order has explicitly not constrained anything, so the order
            # inside one carries no meaning and this loop is free to schedule for throughput.
            # It does that by never leaving this process idle while it still has work: fill
            # every subprocess slot first, then run in-process tests in the time those
            # subprocesses take, and only block once there is nothing left to overlap with.
            for group in _order_marker_groups(session.items):
                # Crossing an ordering boundary: everything started so far has to finish before
                # anything on the far side of the boundary begins. One drain covers both leaving
                # a group -- so @pytest.mark.order(before="NAME") completes first -- and entering
                # one, so @pytest.mark.order(<ORDINAL>) and @pytest.mark.order(after="NAME") see
                # the tests they were sorted behind already finished.
                while running:
                    self._wait_for_jobs(running, session)

                # Tests using the "robot" fixture go to isolated subprocesses, everything else
                # runs here. Both are queues the loop below drains against each other.
                isolated = deque(i for i in group if "robot" in i.fixturenames)
                in_process = deque(i for i in group if "robot" not in i.fixturenames)

                while isolated or in_process:
                    # Reap whatever has already finished so its slot can be reused. This has to
                    # be a poll rather than a wait: slots only free up inside _wait_for_jobs, so
                    # without this a long run of in-process tests would hold the subprocess count
                    # at its high-water mark and refuse to start anything new.
                    self._wait_for_jobs(running, session, timeout=0)

                    while isolated and len(running) < self._parallelism:
                        running.append(self._start_isolated_test(isolated.popleft()))
                        self._maybe_raise(session)

                    if in_process:
                        item = in_process.popleft()

                        # nextitem is pytest's teardown-optimization hint. These run back to
                        # back, so whatever is left at the front always qualifies; the last
                        # test hands over None because the group is drained after it.
                        nextitem = in_process[0] if in_process else None

                        session.config.hook.pytest_runtest_protocol(
                            item=item, nextitem=nextitem
                        )
                        self._maybe_raise(session)
                    elif running:
                        # Every slot is busy and there is no in-process work left to fill the
                        # wait with, so there is nothing to do but block.
                        self._wait_for_jobs(running, session)

            while running:
                self._wait_for_jobs(running, session)
        finally:
            for job in running:
                self._cleanup_job(job)

        return True

    def _start_isolated_test(self, item: pytest.Function) -> IsolatedTestJob:

        config_args = self._config.invocation_params.args
        if self._builtin_tests:
            nodeid = f"{config_args[0]}::{item.name}"
            config_args = config_args[1:]
        else:
            nodeid = item.nodeid

        pconn, cconn = multiprocessing.Pipe()
        process = multiprocessing.Process(
            target=_run_test,
            args=(
                nodeid,
                config_args,
                pickle.dumps(self._robot_class),
                self._robot_file,
                self._verbose,
                cconn,
                self._config.rootpath,
            ),
        )
        process.start()
        cconn.close()

        return IsolatedTestJob(
            item=item,
            conn=pconn,
            process=process,
            start_time=time.time(),
        )

    def _wait_for_jobs(
        self,
        running: list[IsolatedTestJob],
        session: pytest.Session,
        timeout: float | None = None,
    ):
        """
        Collect results from finished jobs, removing them from `running`.

        Blocks until at least one job has something to say. Pass timeout=0 to
        poll instead, which reaps whatever has already finished and returns
        immediately -- used to free subprocess slots without stalling this
        process while it still has in-process tests to run.
        """
        if not running:
            return

        ready = multiprocessing.connection.wait(
            [job.conn for job in running], timeout=timeout
        )

        for conn in ready:
            job = next(job for job in running if job.conn == conn)
            self._process_job_messages(job, session)
            if job.finished:
                running.remove(job)
                self._finalize_job(job, session)

    def _process_job_messages(self, job: IsolatedTestJob, session: pytest.Session):
        while not job.finished:
            try:
                if not job.conn.poll():
                    break
                callname, kwargs = job.conn.recv()
            except (IOError, EOFError) as e:
                job.finished = True
                break

            method = "worker_" + callname
            call = getattr(self, method)
            call(job, **kwargs)
            self._maybe_raise(session)

        if not job.process.is_alive():
            job.finished = True

    def _finalize_job(self, job: IsolatedTestJob, session: pytest.Session):
        self._cleanup_job(job)

        if job.worker_completed:
            return

        stop = time.time()
        duration = stop - job.start_time

        ec = job.exit_code
        longrepr = None
        if ec is None:
            longrepr = "subprocess failed for unknown reason"
        else:
            if ec < 0:
                try:
                    signal_name = signal.strsignal(-ec)
                    longrepr = f"subprocess exited due to signal {-ec}: {signal_name}"
                except ValueError:
                    pass

            if longrepr is None:
                longrepr = f"subprocess exited with exit code {ec}"

        report = pytest.TestReport(
            nodeid=job.item.nodeid,
            location=job.item.location,
            keywords=job.item.keywords,
            outcome="failed",
            longrepr=longrepr,
            when="call",
            duration=duration,
            start=job.start_time,
            stop=stop,
        )

        self._config.hook.pytest_runtest_logstart(
            nodeid=job.item.nodeid, location=job.item.location
        )
        self._config.hook.pytest_runtest_logreport(report=report)
        self._config.hook.pytest_runtest_logfinish(
            nodeid=job.item.nodeid, location=job.item.location
        )

        self._maybe_raise(session)

    def _cleanup_job(self, job: IsolatedTestJob):
        try:
            job.conn.close()
        except Exception:
            pass

        if job.process.is_alive():
            job.process.kill()

        try:
            job.process.join(timeout=1)
        except TimeoutError:
            pass

        ec = job.process.exitcode
        if ec is not None:
            job.set_exit_code(ec)

        job.process.close()

    def _maybe_raise(self, session: pytest.Session):
        if self._shouldstop:
            raise session.Interrupted(self._shouldstop)
        if session.shouldfail:
            raise session.Failed(session.shouldfail)
        if session.shouldstop:
            raise session.Interrupted(session.shouldstop)

    #
    # Worker dispatch functions (copied from pytest-xdist)
    #

    def worker_logstart(
        self,
        job: IsolatedTestJob,
        nodeid: str,
        location: tuple[str, int | None, str],
    ):
        """Emitted when a node calls the pytest_runtest_logstart hook."""
        if self._config.option.verbose > 0:
            return
        self._config.hook.pytest_runtest_logstart(nodeid=nodeid, location=location)

    def worker_logfinish(
        self,
        job: IsolatedTestJob,
        nodeid: str,
        location: tuple[str, int | None, str],
    ):
        """Emitted when a node calls the pytest_runtest_logfinish hook."""
        if self._config.option.verbose > 0:
            return
        self._config.hook.pytest_runtest_logfinish(nodeid=nodeid, location=location)

    def worker_testreport(self, job: IsolatedTestJob, data: object):
        """Emitted when a node calls the pytest_runtest_logreport hook."""

        report = self._config.hook.pytest_report_from_serializable(
            config=self._config, data=data
        )
        self._config.hook.pytest_runtest_logreport(report=report)
        self._handlefailures(report)

    def worker_internal_error(self, job: IsolatedTestJob, formatted_error: str):
        """Emitted when a node calls the pytest_internalerror hook."""
        for line in formatted_error.split("\n"):
            print("IERROR>", line, file=sys.stderr)

        job.finished = True
        if not self._shouldstop:
            self._shouldstop = "internal error in worker"

    def worker_finished(self, job: IsolatedTestJob, exit_code: object | None = None):
        """Emitted when a node finishes running."""
        if exit_code is not None:
            job.exit_code = int(exit_code)

        job.worker_completed = True
        job.finished = True

    def _handlefailures(self, rep: pytest.TestReport):
        if rep.failed:
            self._countfailures += 1
            if (
                self._maxfail
                and self._countfailures >= self._maxfail
                and not self._shouldstop
            ):
                self._shouldstop = f"stopping after {self._countfailures} failures"

    #
    # These fixtures match the ones in RobotTestingPlugin but these have no effect
    #

    @pytest.fixture(scope="function")
    def robot(self):
        pass

    @pytest.fixture(scope="function")
    def control(self, reraise, robot):
        pass

    @pytest.fixture()
    def robot_file(self) -> pathlib.Path:
        """The absolute filename your robot code is started from"""
        return self._robot_file

    @pytest.fixture()
    def robot_path(self) -> pathlib.Path:
        """The absolute directory that your robot code is located at"""
        return self._robot_file.parent
