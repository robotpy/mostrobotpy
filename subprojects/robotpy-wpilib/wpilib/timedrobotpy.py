from sys import argv
from typing import Any, Callable, Iterable, ClassVar
from heapq import heappush, heappop, _siftup
from hal import (
    report,
    initializeNotifier,
    setNotifierName,
    observeUserProgramStarting,
    updateNotifierAlarm,
    waitForNotifierAlarm,
    stopNotifier,
    tResourceType,
    tInstances,
)
from wpilib import RobotController
import wpimath.units

from .iterativerobotpy import IterativeRobotPy

_getFPGATime = RobotController.getFPGATime
_kResourceType_Framework = tResourceType.kResourceType_Framework
_kFramework_Timed = tInstances.kFramework_Timed

microsecondsAsInt = int


class _Callback:

    def __init__(
        self,
        func: Callable[[], None],
        periodUs: microsecondsAsInt,
        expirationUs: microsecondsAsInt,
    ) -> None:
        self.func = func
        self._periodUs = periodUs
        self.expirationUs = expirationUs

    @classmethod
    def makeCallBack(
        cls,
        func: Callable[[], None],
        startTimeUs: microsecondsAsInt,
        periodUs: microsecondsAsInt,
        offsetUs: microsecondsAsInt,
        currentTimeUs: microsecondsAsInt,
    ) -> "_Callback":

        callback = _Callback(func=func, periodUs=periodUs, expirationUs=startTimeUs)

        callback.expirationUs = offsetUs + callback.calcFutureExpirationUs(
            currentTimeUs
        )
        return callback

    def calcFutureExpirationUs(
        self, currentTimeUs: microsecondsAsInt
    ) -> microsecondsAsInt:
        # increment the expiration time by the number of full periods it's behind
        # plus one to avoid rapid repeat fires from a large loop overrun.
        #
        # This routine is called when either:
        #   this callback has never ran and self.expirationUs is
        #   TimedRobot._starttimeUs and we are calculating where the first
        #   expiration should be relative to TimedRobot._starttimeUs
        # or:
        #   this call back has ran and self.expirationUs is when it was scheduled to
        #   expire and we are calculating when the next expirations should be relative
        #   to the last scheduled expiration
        #
        # We assume currentTime ≥ self.expirationUs rather than checking for it since the
        # callback wouldn't be running otherwise.
        #
        # We take when we previously expired or when we started: self.expirationUs
        # add + self._periodUs to get at least one period in the future
        # then calculate how many whole periods we are behind:
        #   ((currentTimeUs - self.expirationUs) // self._periodUs)
        # and multiply that by self._periodUs to calculate how much time in full
        # periods we need to skip to catch up, and add that to the sum to calculate
        # when we should run again.
        return (
            self.expirationUs
            + self._periodUs
            + ((currentTimeUs - self.expirationUs) // self._periodUs) * self._periodUs
        )

    def setOrderedFieldNextExpirationUs(self, currentTimeUs: microsecondsAsInt) -> None:
        self.expirationUs = self.calcFutureExpirationUs(currentTimeUs)

    def __lt__(self, other) -> bool:
        return self.expirationUs < other.expirationUs

    def __bool__(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"{{func={self.func.__name__}, _periodUs={self._periodUs}, expirationUs={self.expirationUs}}}"


class _OrderedListSort:

    def __init__(self) -> None:
        self._data: list[Any] = []

    def add(self, item: Any) -> None:
        self._data.append(item)
        self._data.sort()

    def peek(self) -> Any:
        return self._data[0]

    def reorderListAfterAChangeInTheFirstElement(self):
        self._data.sort()

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterable[Any]:
        return iter(sorted(self._data))

    def __contains__(self, item) -> bool:
        return item in self._data

    def __repr__(self) -> str:
        return str(sorted(self._data))


class _OrderedListMin:

    def __init__(self) -> None:
        self._data: list[Any] = []

    def add(self, item: Any) -> None:
        self._data.append(item)

    def peek(self) -> Any:
        return min(self._data)

    def reorderListAfterAChangeInTheFirstElement(self):
        pass

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterable[Any]:
        return iter(sorted(self._data))

    def __contains__(self, item) -> bool:
        return item in self._data

    def __repr__(self) -> str:
        return str(sorted(self._data))


class _OrderedListHeapq:

    def __init__(self) -> None:
        self._data: list[Any] = []

    def add(self, item: Any) -> None:
        heappush(self._data, item)

    def peek(self) -> Any:
        return self._data[0]

    def reorderListAfterAChangeInTheFirstElement(self):
        _siftup(self._data, 0)

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterable[Any]:
        return iter(sorted(self._data))

    def __contains__(self, item) -> bool:
        return item in self._data

    def __repr__(self) -> str:
        return str(sorted(self._data))


# Hooks to use timeit to evaluate configurations of TimedRobotPy
_OrderedList = _OrderedListMin
_initializeNotifier = initializeNotifier
_setNotifierName = setNotifierName
_observeUserProgramStarting = observeUserProgramStarting
_updateNotifierAlarm = updateNotifierAlarm
_waitForNotifierAlarm = waitForNotifierAlarm
_stopNotifier = stopNotifier
_report = report
_IterativeRobotPy = IterativeRobotPy
if "_IterativeRobotPyIsObject" in argv:
    print("_IterativeRobotPyIsObject")
    _IterativeRobotPy = object


# todo what should the name of this class be?
class TimedRobotPy(_IterativeRobotPy):
    """
    TimedRobotPy implements the IterativeRobotBase robot program framework.

    The TimedRobotPy class is intended to be subclassed by a user creating a
    robot program.

    Periodic() functions from the base class are called on an interval by a
    Notifier instance.
    """

    kDefaultPeriod: ClassVar[wpimath.units.seconds] = (
        0.020  # todo this is a change to keep consistent units in the API
    )

    def __init__(self, period: wpimath.units.seconds = kDefaultPeriod) -> None:
        """
        Constructor for TimedRobotPy.

        :param period: period of the main robot periodic loop in seconds.
        """
        if "_IterativeRobotPyIsObject" in argv:
            super().__init__()
            self._periodS = period
        else:
            super().__init__(period)

        # All periodic functions created by addPeriodic are relative
        # to this self._startTimeUs
        self._startTimeUs = _getFPGATime()
        self._callbacks = _OrderedList()
        self._loopStartTimeUs = 0
        self.addPeriodic(self._loopFunc, period=self._periodS)

        self._notifier, status = _initializeNotifier()
        if status != 0:
            raise RuntimeError(
                f"initializeNotifier() returned {self._notifier}, {status}"
            )

        status = _setNotifierName(self._notifier, "TimedRobotPy")
        if status != 0:
            raise RuntimeError(f"setNotifierName() returned {status}")

        _report(_kResourceType_Framework, _kFramework_Timed)

    def startCompetition(self) -> None:
        """
        Provide an alternate "main loop" via startCompetition().
        """
        try:
            self.robotInit()

            if self.isSimulation():
                self._simulationInit()

            # Tell the DS that the robot is ready to be enabled
            print("********** Robot program startup complete **********", flush=True)
            _observeUserProgramStarting()

            # Loop forever, calling the appropriate mode-dependent function
            # (really not forever, there is a check for a stop)
            while self._bodyOfMainLoop():
                pass
        finally:
            # pytests hang on PC when we don't force a call to self._stopNotifier()
            self._stopNotifier()

    def _bodyOfMainLoop(self) -> bool:
        keepGoing = True
        #  We don't have to check there's an element in the queue first because
        #  there's always at least one (the constructor adds one).
        callback = self._callbacks.peek()

        status = _updateNotifierAlarm(self._notifier, callback.expirationUs)
        if status != 0:
            raise RuntimeError(f"updateNotifierAlarm() returned {status}")

        self._loopStartTimeUs, status = _waitForNotifierAlarm(self._notifier)

        # The C++ code that this was based upon used the following line to establish
        # the loopStart time. Uncomment it and
        # the "self._loopStartTimeUs = startTimeUs" further below to emulate the
        # legacy behavior.
        # startTimeUs = _getFPGATime() # uncomment this for legacy behavior

        if status != 0:
            raise RuntimeError(
                f"waitForNotifierAlarm() returned _loopStartTimeUs={self._loopStartTimeUs} status={status}"
            )

        if self._loopStartTimeUs == 0:
            # when HAL_StopNotifier(self.notifier) is called the above waitForNotifierAlarm
            # will return a _loopStartTimeUs==0 and the API requires robots to stop any loops.
            # See the API for waitForNotifierAlarm
            keepGoing = False
            return keepGoing

        # On a RoboRio 2, the following print statement results in values like:
        # print(f"expUs={callback.expirationUs} current={self._loopStartTimeUs}, legacy={startTimeUs}")
        # [2.27] expUs=3418017 current=3418078, legacy=3418152
        # [2.29] expUs=3438017 current=3438075, legacy=3438149
        # This indicates that there is about 60 microseconds of skid from
        # callback.expirationUs to self._loopStartTimeUs
        # and there is about 70 microseconds of skid from self._loopStartTimeUs to startTimeUs.
        # Consequently, this code uses "self._loopStartTimeUs, status = waitForNotifierAlarm"
        # to establish loopStartTime, rather than slowing down the code by adding an extra call to
        # "startTimeUs = _getFPGATime()".

        # self._loopStartTimeUs = startTimeUs # Uncomment this line for legacy behavior.

        self._runCallbackAtHeadOfListAndReschedule(callback)

        # Process all other callbacks that are ready to run
        # Changing the comparison to be _getFPGATime() rather than
        # self._loopStartTimeUs would also be correct.
        while (callback := self._callbacks.peek()).expirationUs <= _getFPGATime():
            self._runCallbackAtHeadOfListAndReschedule(callback)

        return keepGoing

    def _runCallbackAtHeadOfListAndReschedule(self, callback) -> None:
        # The callback.func() may have added more callbacks to self._callbacks,
        # but each is sorted by the _getFPGATime() at the moment it is
        # created, which is greater than self.expirationUs of this callback,
        # so this callback remains at the head of the list, so we can
        # use this peeked reference to it.
        callback.func()
        # The c++ implementation used the current time before the callback ran,
        # to reschedule. By using _getFPGATime(), on a callback.func()
        # that ran long we immediately push the next invocation to the
        # following period.
        callback.setOrderedFieldNextExpirationUs(_getFPGATime())
        # assert callback is self._callbacks.peek()
        #
        # Because any added callback is after this callback, this
        # callback is at the head of the list, so we can just
        # reorder the list due to a first element change, without
        # a full resort of the list.
        self._callbacks.reorderListAfterAChangeInTheFirstElement()

    def _stopNotifier(self):
        _stopNotifier(self._notifier)

    def endCompetition(self) -> None:
        """
        Ends the main loop in startCompetition().
        """
        self._stopNotifier()

    def getLoopStartTime(self) -> microsecondsAsInt:
        """
        Return the system clock time in microseconds
        for the start of the current
        periodic loop. This is in the same time base as Timer.getFPGATimestamp(),
        but is stable through a loop. It is updated at the beginning of every
        periodic callback (including the normal periodic loop).

        :returns: Robot running time in microseconds,
                  as of the start of the current
                  periodic function.
        """

        return self._loopStartTimeUs

    def addPeriodic(
        self,
        callback: Callable[[], None],
        period: wpimath.units.seconds,
        offset: wpimath.units.seconds = 0.0,
    ) -> None:
        """
        Add a callback to run at a specific period with a starting time offset.

        This is scheduled on TimedRobotPy's Notifier, so TimedRobotPy and the callback
        run synchronously. Interactions between them are thread-safe.

        :param callback: The callback to run.
        :param period:   The period at which to run the callback.
        :param offset:   The offset from the common starting time. This is useful
                         for scheduling a callback in a different timeslot relative
                         to TimedRobotPy.
        """
        currentTimeUs = _getFPGATime()
        cb = _Callback.makeCallBack(
            callback,
            self._startTimeUs,
            int(period * 1e6),
            int(offset * 1e6),
            currentTimeUs,
        )
        if len(self._callbacks):
            # This addPeriodic method may be called from within a callback.func()
            # from the callback that is at the head of self._callbacks list. Because
            # currentTimeUs and cb.expirationUs are greater than
            # self._callbacks.peek().expirationUs we know that the
            # self._callbacks.add(cb) will not change self._callbacks.peek()
            # The self._runCallbackAtHeadOfListAndReschedule() depends on this
            # when rescheduling the callback at the head of self._callbacks.
            assert cb > self._callbacks.peek()
        self._callbacks.add(cb)
