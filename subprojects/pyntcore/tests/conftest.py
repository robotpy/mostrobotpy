#
# Useful fixtures
#

from contextlib import contextmanager
from threading import Condition

from ntcore._ntcore import ValueListenerFlags

log_datefmt = "%H:%M:%S"
log_format = "%(asctime)s:%(msecs)03d %(levelname)-8s: %(name)-8s: %(message)s"

import logging

logging.basicConfig(level=logging.DEBUG, format=log_format, datefmt=log_datefmt)


logger = logging.getLogger("conftest")

import pytest

from ntcore import NetworkTableInstance, ValueListener, MultiSubscriber

#
# Fixtures for a usable in-memory version of networktables
#


@pytest.fixture(scope="function")
def nt():
    instance = NetworkTableInstance.create()
    instance.startLocal()

    try:
        yield instance
    finally:
        NetworkTableInstance.destroy(instance)


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
        self._wait_lock = Condition()
        self._wait = 0
        self._wait_init_listener()

    def _wait_init_listener(self):

        self.msub = MultiSubscriber(self._impl, ["/"])
        self.vl = ValueListener(self.msub, ValueListenerFlags.kImmediate, self._wait_cb)
        logger.info("wait init")

        # self._impl.addEntryListener(
        #     "",
        #     self._wait_cb,
        #     NetworkTableInstance.NotifyFlags.NEW
        #     | NetworkTableInstance.NotifyFlags.UPDATE
        #     | NetworkTableInstance.NotifyFlags.DELETE
        #     | NetworkTableInstance.NotifyFlags.FLAGS,
        # )

    def _wait_cb(self, *args):
        logger.info('Wait callback, got: %s', args)
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
            result, msg = (
                self._wait_lock.wait_for(lambda: self._wait == count, 4),
                "Timeout waiting for %s changes (got %s)" % (count, self._wait),
            )
            logger.info("expect_changes: %s %s", result, msg)
            assert result, msg


@pytest.fixture()
def nt_server(request):
    class NtServer(NtTestBase):

        _test_saved_port3 = None
        _test_saved_port4 = None

        def start_test(self):
            logger.info("NtServer::start_test")

            # Restore server port on restart
            if self._test_saved_port3 is not None:
                self.port3 = self._test_saved_port3
                self.port4 = self._test_saved_port4

            print("self.port", self.port3, self.port4)
            self._impl.startServer(listen_address="127.0.0.1", port3=self.port3, port4=self.port4)

            # assert self._api.dispatcher.m_server_acceptor.waitForStart(timeout=1)
            # self.port = self._api.dispatcher.m_server_acceptor.m_port
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
            self._impl.setServer("127.0.0.1", nt_server.port3)
            self._impl.startClient3()

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
            self._impl.setNetworkIdentity("C4")
            self._impl.setServer("127.0.0.1", nt_server.port4)
            self._impl.startClient4()

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
