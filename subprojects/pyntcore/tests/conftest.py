#
# Useful fixtures
#

from contextlib import contextmanager
from threading import Condition

import logging

logger = logging.getLogger("conftest")

import pytest

from ntcore import NetworkTableInstance, MultiSubscriber, Event, EventFlags

#
# Fixtures for a usable in-memory version of networktables
#


@pytest.fixture
def cfg_logging(caplog):
    caplog.set_level(logging.INFO)


@pytest.fixture(scope="function")
def nt(cfg_logging):
    instance = NetworkTableInstance.create()
    instance.startLocal()

    try:
        yield instance
    finally:
        NetworkTableInstance.destroy(instance)


#
# Live NT instance fixtures
#


class NtTestBase:
    """
    Object for managing a live pair of NT server/client
    """

    _wait_lock = None

    def __init__(self):
        self.reset()

    def reset(self):
        self._impl = NetworkTableInstance.create()
        self.getTable = self._impl.getTable
        self.isConnected = self._impl.isConnected

    def shutdown(self):
        logger.info("shutting down %s", self.__class__.__name__)
        if self._impl:
            NetworkTableInstance.destroy(self._impl)
        self._impl = None

    # def disconnect(self):
    #     self._api.dispatcher.stop()

    def _init_common(self):
        # This resets the instance to be independent
        self.shutdown()
        self.reset()

        # self._wait_init()

    def _init_server(self, port3=23232, port4=23233):
        self._init_common()

        self.port3 = port3
        self.port4 = port4

    def _init_client(self):
        self._init_common()

    def _wait_init(self):
        logger.info("wait-init %s", self.__class__.__name__)
        self._wait_lock = Condition()
        self._wait = 0

        self.msub = MultiSubscriber(self._impl, [""])
        self.vl = self._impl.addListener(
            self.msub, EventFlags.kValueRemote, self._wait_cb
        )

    def _wait_cb(self, evt: Event):
        logger.info("wait-callback %s: %s", self.__class__.__name__, evt)
        with self._wait_lock:
            self._wait += 1
            self._wait_lock.notify()

    @contextmanager
    def expect_changes(self, count):
        """Use this on the *other* instance that you're making
        changes on, to wait for the changes to propagate to the
        other instance"""

        if self._wait_lock is None:
            self._wait_init()

        with self._wait_lock:
            self._wait = 0

        logger.info("Begin actions")
        yield
        logger.info("Waiting for %s changes", count)

        with self._wait_lock:
            self._wait_lock.wait_for(lambda: self._wait >= count, 4)
            logger.info("expect_changes: %s == %s", self._wait, count)

            msg = "Failed waiting for exactly %s changes (got %s)" % (count, self._wait)
            assert self._wait == count, msg


@pytest.fixture()
def nt_server(request, cfg_logging):
    class NtServer(NtTestBase):
        _test_saved_port3 = None
        _test_saved_port4 = None

        def start_test(self):
            logger.info("NtServer::start_test")

            # Restore server port on restart
            if self._test_saved_port3 is not None:
                self.port3 = self._test_saved_port3
                self.port4 = self._test_saved_port4

            self._impl.startServer(
                listen_address="127.0.0.1", port3=self.port3, port4=self.port4
            )

            self._test_saved_port3 = self.port3
            self._test_saved_port4 = self.port4

    server = NtServer()
    server._init_server()
    try:
        yield server
    finally:
        server.shutdown()


@pytest.fixture()
def nt_client3(request, nt_server):
    class NtClient(NtTestBase):
        def start_test(self):
            self._impl.startClient3("C3")
            self._impl.setServer("127.0.0.1", nt_server.port3)

    client = NtClient()
    client._init_client()
    try:
        yield client
    finally:
        client.shutdown()


@pytest.fixture()
def nt_client4(request, nt_server):
    class NtClient(NtTestBase):
        def start_test(self):
            self._impl.startClient4("C4")
            self._impl.setServer("127.0.0.1", nt_server.port4)

    client = NtClient()
    client._init_client()
    yield client
    client.shutdown()


@pytest.fixture
def nt_live(nt_server, nt_client4):
    """This fixture automatically starts the client and server"""

    nt_server.start_test()
    nt_client4.start_test()

    return nt_server, nt_client4
