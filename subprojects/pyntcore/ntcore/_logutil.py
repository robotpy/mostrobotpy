import atexit
import logging
import threading

from . import _ntcore

import wpiutil.sync


class NtLogForwarder:
    """
    Forwards ntcore's logger to python's logging system
    """

    _instlock = threading.Lock()
    _instances = {}

    @classmethod
    def attach(cls, instHandle):
        # TODO: allow customizing the name, log levels?
        with cls._instlock:
            if instHandle in cls._instances:
                return

            cls._instances[instHandle] = cls(instHandle, "nt")

    @classmethod
    def detach(cls, instHandle):
        with cls._instlock:
            lfwd = cls._instances.pop(instHandle, None)
            if lfwd:
                lfwd.destroy()

    def __init__(
        self,
        instHandle,
        logName: str,
        minLevel=_ntcore.NetworkTableInstance.LogLevel.kLogDebug,
        maxLevel=_ntcore.NetworkTableInstance.LogLevel.kLogCritical,
    ):
        self.lock = threading.Lock()
        self.poller = _ntcore._createLoggerPoller(instHandle)
        ntLogger = _ntcore._addPolledLogger(self.poller, minLevel, maxLevel)

        self.thread = threading.Thread(
            target=self._logging_thread,
            name=logName + "-log-thread",
            daemon=True,
            args=(self.poller, logName, ntLogger),
        )
        self.thread.start()

        atexit.register(self.destroy)

    def _logging_thread(self, poller: int, logName: str, ntLogger: int):

        logger = logging.getLogger(logName)

        _readLoggerQueue = _ntcore._readLoggerQueue
        _waitForObject = wpiutil.sync.waitForObject

        while True:
            if not _waitForObject(poller):
                break

            messages = _readLoggerQueue(poller)
            if not messages:
                continue

            for msg in messages:
                if logger.isEnabledFor(msg.level):
                    lr = logger.makeRecord(
                        logName,
                        msg.level,
                        msg.filename,
                        msg.line,
                        "%s",
                        (msg.message,),
                        None,
                    )
                    logger.handle(lr)

        _ntcore._removeLogger(ntLogger)

    def destroy(self):
        with self.lock:
            if self.poller:
                _ntcore._destroyLoggerPoller(self.poller)
                self.thread.join(timeout=1)
            self.poller = None


_attach = NtLogForwarder.attach
_detach = NtLogForwarder.detach
