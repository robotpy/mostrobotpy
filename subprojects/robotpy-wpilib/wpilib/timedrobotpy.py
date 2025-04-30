from typing import Any, Callable, Iterable, ClassVar
from heapq import heappush, heappop
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
    ) -> "_Callback":

        callback = _Callback(func=func, periodUs=periodUs, expirationUs=startTimeUs)

        currentTimeUs = _getFPGATime()
        callback.expirationUs = offsetUs + callback.calcFutureExpirationUs(
            currentTimeUs
        )
        return callback

    def calcFutureExpirationUs(
        self, currentTimeUs: microsecondsAsInt
    ) -> microsecondsAsInt:
        # increment the expiration time by the number of full periods it's behind
        # plus one to avoid rapid repeat fires from a large loop overrun. We assume
        # currentTime ≥ startTimeUs rather than checking for it since the
        # callback wouldn't be running otherwise.
        # todo does this math work?
        # todo does the "// periodUs * periodUs" do the correct integer math?
        return (
            self.expirationUs
            + self._periodUs
            + ((currentTimeUs - self.expirationUs) // self._periodUs) * self._periodUs
        )

    def setNextStartTimeUs(self, currentTimeUs: microsecondsAsInt) -> None:
        self.expirationUs = self.calcFutureExpirationUs(currentTimeUs)

    def __lt__(self, other) -> bool:
        return self.expirationUs < other.expirationUs

    def __bool__(self) -> bool:
        return True


class _OrderedList:
    def __init__(self) -> None:
        self._data: list[Any] = []

    def add(self, item: Any) -> None:
        heappush(self._data, item)

    def pop(self) -> Any:
        return heappop(self._data)

    def peek(self) -> Any | None:
        if self._data:
            return self._data[0]
        else:
            return None

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterable[Any]:
        return iter(sorted(self._data))

    def __contains__(self, item) -> bool:
        return item in self._data

    def __str__(self) -> str:
        return str(sorted(self._data))


# todo what should the name of this class be?
class TimedRobotPy(IterativeRobotPy):
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
        super().__init__(period)

        self._startTimeUs = _getFPGATime()
        self._callbacks = _OrderedList()
        self._loopStartTimeUs = 0
        self.addPeriodic(self._loopFunc, period=self._periodS)

        self._notifier, status = initializeNotifier()
        if status != 0:
            raise RuntimeError(
                f"initializeNotifier() returned {self._notifier}, {status}"
            )

        status = setNotifierName(self._notifier, "TimedRobotPy")
        if status != 0:
            raise RuntimeError(f"setNotifierName() returned {status}")

        report(_kResourceType_Framework, _kFramework_Timed)

    def startCompetition(self) -> None:
        """
        Provide an alternate "main loop" via startCompetition().
        """
        self.robotInit()

        if self.isSimulation():
            self._simulationInit()

        # Tell the DS that the robot is ready to be enabled
        print("********** Robot program startup complete **********")
        observeUserProgramStarting()

        # Loop forever, calling the appropriate mode-dependent function
        # (really not forever, there is a check for a break)
        while True:
            #  We don't have to check there's an element in the queue first because
            #  there's always at least one (the constructor adds one). It's re-enqueued
            #  at the end of the loop.
            callback = self._callbacks.pop()

            status = updateNotifierAlarm(self._notifier, callback.expirationUs)
            if status != 0:
                raise RuntimeError(f"updateNotifierAlarm() returned {status}")

            currentTimeUs, status = waitForNotifierAlarm(self._notifier)
            if status != 0:
                raise RuntimeError(
                    f"waitForNotifierAlarm() returned currentTimeUs={currentTimeUs} status={status}"
                )

            if currentTimeUs == 0:
                # when HAL_StopNotifier(self.notifier) is called the above waitForNotifierAlarm
                # will return a currentTimeUs==0 and the API requires robots to stop any loops.
                # See the API for waitForNotifierAlarm
                break

            self._loopStartTimeUs = _getFPGATime()
            self._runCallbackAndReschedule(callback, currentTimeUs)

            #  Process all other callbacks that are ready to run
            while self._callbacks.peek().expirationUs <= currentTimeUs:
                callback = self._callbacks.pop()
                self._runCallbackAndReschedule(callback, currentTimeUs)

    def _runCallbackAndReschedule(
        self, callback: _Callback, currentTimeUs: microsecondsAsInt
    ) -> None:
        callback.func()
        callback.setNextStartTimeUs(currentTimeUs)
        self._callbacks.add(callback)

    def endCompetition(self) -> None:
        """
        Ends the main loop in startCompetition().
        """
        stopNotifier(self._notifier)

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

        self._callbacks.add(
            _Callback.makeCallBack(
                callback, self._startTimeUs, int(period * 1e6), int(offset * 1e6)
            )
        )
