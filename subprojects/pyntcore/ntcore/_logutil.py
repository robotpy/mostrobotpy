import atexit
import logging
import threading

from . import _ntcore

import wpiutil.sync


class InstanceAlreadyStartedError(Exception):
    pass


class NtLogForwarder:
    """
    Forwards ntcore's logger to python's logging system
    """

    _instlock = threading.Lock()
    _instances = {}
    _instcfg = {}

    @classmethod
    def config_logging(
        cls,
        instHandle: int,
        minLevel: _ntcore.NetworkTableInstance.LogLevel,
        maxLevel: _ntcore.NetworkTableInstance.LogLevel,
        logName: str,
    ):
        with cls._instlock:
            if instHandle in cls._instances:
                raise InstanceAlreadyStartedError(
                    "cannot configure logging after instance has been started"
                )

            cls._instcfg[instHandle] = (minLevel, maxLevel, logName)

    @classmethod
    def attach(cls, instHandle: int):
        with cls._instlock:
            if instHandle in cls._instances:
                return

            default_cfg = (
                _ntcore.NetworkTableInstance.LogLevel.kLogInfo,
                _ntcore.NetworkTableInstance.LogLevel.kLogCritical,
                "nt",
            )
            minLevel, maxLevel, logName = cls._instcfg.get(instHandle, default_cfg)

            cls._instances[instHandle] = cls(instHandle, logName, minLevel, maxLevel)

    @classmethod
    def detach(cls, instHandle):
        with cls._instlock:
            lfwd = cls._instances.pop(instHandle, None)
            if lfwd:
                lfwd.destroy()

    def __init__(
        self,
        instHandle: int,
        logName: str,
        minLevel: _ntcore.NetworkTableInstance.LogLevel,
        maxLevel: _ntcore.NetworkTableInstance.LogLevel,
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

        try:
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
        finally:
            _ntcore._removeLogger(ntLogger)

    def destroy(self):
        with self.lock:
            if self.poller:
                _ntcore._destroyLoggerPoller(self.poller)
                self.thread.join(timeout=1)
            self.poller = None


_attach = NtLogForwarder.attach
_detach = NtLogForwarder.detach
_config_logging = NtLogForwarder.config_logging
