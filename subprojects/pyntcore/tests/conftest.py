#
# Useful fixtures
#

from contextlib import contextmanager
from threading import Condition

log_datefmt = "%H:%M:%S"
log_format = "%(asctime)s:%(msecs)03d %(levelname)-8s: %(name)-8s: %(message)s"

import logging

logging.basicConfig(level=logging.DEBUG, format=log_format, datefmt=log_datefmt)


logger = logging.getLogger("conftest")

import pytest

from _pyntcore import NetworkTablesInstance

#
# Fixtures for a usable in-memory version of networktables
#


@pytest.fixture(scope="function")
def nt():
    instance = NetworkTablesInstance.create()
    instance.startLocal()

    try:
        yield instance
    finally:
        NetworkTablesInstance.destroy(instance)


@pytest.fixture(scope="function")
def nt_flush(nt):
    """Flushes NT key notifications"""

    def _flush():
        assert nt.waitForEntryListenerQueue(1.0)
        assert nt.waitForConnectionListenerQueue(1.0)

    return _flush


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
        self._impl = NetworkTablesInstance.create()
        self.getTable = self._impl.getTable
        self.isConnected = self._impl.isConnected

    def shutdown(self):
        logger.info("shutting down %s", self.__class__.__name__)
        if self._impl:
            NetworkTablesInstance.destroy(self._impl)
        self._impl = None

    # def disconnect(self):
    #     self._api.dispatcher.stop()

    def _init_common(self):
        # This resets the instance to be independent
        self.shutdown()
        self.reset()

        # self._wait_init()

    def _init_server(self, server_port=23232):
        self._init_common()

        self.port = server_port

    def _init_client(self):
        self._init_common()

    def _wait_init(self):
        self._wait_lock = Condition()
        self._wait = 0
        self._wait_init_listener()

    def _wait_init_listener(self):
        self._impl.addEntryListener(
            "",
            self._wait_cb,
            NetworkTablesInstance.NotifyFlags.NEW
            | NetworkTablesInstance.NotifyFlags.UPDATE
            | NetworkTablesInstance.NotifyFlags.DELETE
            | NetworkTablesInstance.NotifyFlags.FLAGS,
        )

    def _wait_cb(self, *args):
        with self._wait_lock:
            self._wait += 1
            # logger.info('Wait callback, got: %s', args)
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
            result, msg = (
                self._wait_lock.wait_for(lambda: self._wait == count, 4),
                "Timeout waiting for %s changes (got %s)" % (count, self._wait),
            )
            logger.info("expect_changes: %s %s", result, msg)
            assert result, msg


@pytest.fixture()
def nt_server(request):
    class NtServer(NtTestBase):

        _test_saved_port = None

        def start_test(self):
            logger.info("NtServer::start_test")

            # Restore server port on restart
            if self._test_saved_port is not None:
                self.port = self._test_saved_port

            print("self.port", self.port)
            self._impl.startServer(listenAddress="127.0.0.1", port=self.port)

            # assert self._api.dispatcher.m_server_acceptor.waitForStart(timeout=1)
            # self.port = self._api.dispatcher.m_server_acceptor.m_port
            self._test_saved_port = self.port

    server = NtServer()
    server._init_server()
    try:
        yield server
    finally:
        server.shutdown()


@pytest.fixture()
def nt_client(request, nt_server):
    class NtClient(NtTestBase):
        def start_test(self):
            self._impl.setNetworkIdentity("C1")
            self._impl.startClient("127.0.0.1", nt_server.port)

    client = NtClient()
    client._init_client()
    try:
        yield client
    finally:
        client.shutdown()


@pytest.fixture()
def nt_client2(request, nt_server):
    class NtClient(NtTestBase):
        def start_test(self):
            self._impl.setNetworkIdentity("C2")
            self._impl.startClient(("127.0.0.1", nt_server.port))

    client = NtClient()
    client._init_client()
    yield client
    client.shutdown()


@pytest.fixture
def nt_live(nt_server, nt_client):
    """This fixture automatically starts the client and server"""

    nt_server.start_test()
    nt_client.start_test()

    return nt_server, nt_client
