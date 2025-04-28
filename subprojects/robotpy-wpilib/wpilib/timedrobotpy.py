from typing import Any, Callable, Iterable
from heapq import heappush, heappop
from hal import report, initializeNotifier, setNotifierName, observeUserProgramStarting, updateNotifierAlarm, \
    waitForNotifierAlarm, stopNotifier, tResourceType, tInstances
from wpilib import RobotController

from .iterativerobotpy import IterativeRobotPy

_getFPGATime = RobotController.getFPGATime
_kResourceType_Framework = tResourceType.kResourceType_Framework
_kFramework_Timed = tInstances.kFramework_Timed

class _Callback:
    def __init__(self, func: Callable[[],None], periodUs: int, expirationUs: int):
        self.func = func
        self._periodUs = periodUs
        self.expirationUs = expirationUs

    @classmethod
    def makeCallBack(cls,
                     func: Callable[[],None],
                     startTimeUs: int,
                     periodUs: int,
                     offsetUs: int) -> "_Callback":

        callback = _Callback(
            func=func,
            periodUs=periodUs,
            expirationUs=startTimeUs
        )

        currentTimeUs = _getFPGATime()
        callback.expirationUs = offsetUs + callback.calcFutureExpirationUs(currentTimeUs)
        return callback

    def calcFutureExpirationUs(self, currentTimeUs: int) -> int:
        # increment the expiration time by the number of full periods it's behind
        # plus one to avoid rapid repeat fires from a large loop overrun. We assume
        # currentTime ≥ startTimeUs rather than checking for it since the
        # callback wouldn't be running otherwise.
        # todo does this math work?
        # todo does the "// periodUs * periodUs" do the correct integer math?
        return self.expirationUs + self._periodUs + \
            ((currentTimeUs - self.expirationUs) // self._periodUs) * self._periodUs

    def setNextStartTimeUs(self, currentTimeUs: int) -> None:
        self.expirationUs = self.calcFutureExpirationUs(currentTimeUs)

    def __lt__(self, other) -> bool:
        return self.expirationUs < other.expirationUs

    def __bool__(self) -> bool:
        return True


class _OrderedList:
    def __init__(self):
        self._data: list[Any] = []

    def add(self, item: Any) -> None:
        heappush(self._data, item)

    def pop(self) -> Any:
        return heappop(self._data)

    def peek(self) -> Any|None:
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


class TimedRobotPy(IterativeRobotPy):

    def __init__(self, period: float = 0.020):
        super().__init__(period)

        self._startTimeUs = _getFPGATime()
        self._callbacks = _OrderedList()
        self.loopStartTimeUs = 0
        self.addPeriodic(self.loopFunc, period=period)

        self._notifier, status = initializeNotifier()
        if status != 0:
            raise RuntimeError(f"initializeNotifier() returned {self._notifier}, {status}")

        status = setNotifierName(self._notifier, "TimedRobot")
        if status != 0:
            raise RuntimeError(f"setNotifierName() returned {status}")

        report(_kResourceType_Framework, _kFramework_Timed)

    def startCompetition(self) -> None:
        self.robotInit()

        if self.isSimulation():
            self.simulationInit()

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
                raise RuntimeError(f"waitForNotifierAlarm() returned currentTimeUs={currentTimeUs} status={status}")

            if currentTimeUs == 0:
                # when HAL_StopNotifier(self.notifier) is called the above waitForNotifierAlarm
                # will return a currentTimeUs==0 and the API requires robots to stop any loops.
                # See the api for waitForNotifierAlarm
                break

            self.loopStartTimeUs = _getFPGATime()
            self._runCallbackAndReschedule(callback, currentTimeUs)

            #  Process all other callbacks that are ready to run
            while self._callbacks.peek().expirationUs <= currentTimeUs:
                callback = self._callbacks.pop()
                self._runCallbackAndReschedule(callback, currentTimeUs)

    def _runCallbackAndReschedule(self, callback: Callable[[],None], currentTimeUs: int) -> None:
        callback.func()
        callback.setNextStartTimeUs(currentTimeUs)
        self._callbacks.add(callback)

    def endCompetition(self) -> None:
        stopNotifier(self._notifier)

    def getLoopStartTime(self) -> float:
        return self.loopStartTimeUs/1e6  # units are seconds

    def addPeriodic(self,
                    callback: Callable[[],None],
                    period: float, # units are seconds
                    offset: float = 0.0 # units are seconds
                    ) -> None:
        self._callbacks.add(
            _Callback.makeCallBack(
                callback,
                self._startTimeUs, int(period * 1e6), int(offset * 1e6)
            )
        )
