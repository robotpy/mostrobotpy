from heapq import heappush, heappop
from hal import report, initializeNotifier, setNotifierName, observeUserProgramStarting, updateNotifierAlarm, \
    waitForNotifierAlarm, stopNotifier, tResourceType, tInstances
from wpilib import RobotController

from wpilib.iterativerobotpy import IterativeRobotPy

_getFPGATime = RobotController.getFPGATime
_kResourceType_Framework = tResourceType.kResourceType_Framework
_kFramework_Timed = tInstances.kFramework_Timed

class _Callback:
    def __init__(self, func, periodUs: int, expirationUs: int):
        self.func = func
        self._periodUs = periodUs
        self.expirationUs = expirationUs

    @classmethod
    def makeCallBack(cls,
                     func,
                     startTimeUs: int,
                     periodUs: int,
                     offsetUs: int):

        callback = _Callback(
            func,
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

    def setNextStartTimeUs(self, currentTimeUs: int):
        self.expirationUs = self.calcFutureExpirationUs(currentTimeUs)

    def __lt__(self, other):
        return self.expirationUs < other.expirationUs

    def __bool__(self):
        return True


class _OrderedList:
    def __init__(self):
        self._data = []

    def add(self, item):
        heappush(self._data, item)

    def pop(self):
        return heappop(self._data)

    def peek(self):
        if self._data:
            return self._data[0]
        else:
            return None

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(sorted(self._data))

    def __contains__(self, item):
        return item in self._data

    def __str__(self):
        return str(sorted(self._data))


class TimedRobotPy(IterativeRobotPy):

    def __init__(self, periodS: float = 0.020):
        super().__init__(periodS)

        self._startTimeUs = _getFPGATime()
        self._callbacks = _OrderedList()
        self.loopStartTimeUs = 0
        self.addPeriodic(self.loopFunc, period=periodS)

        self._notifier, status = initializeNotifier()
        if status != 0:
            message = f"initializeNotifier() returned {status} {self._notifier}"
            #raise RuntimeError(message) # todo

        status = setNotifierName(self._notifier, "TimedRobot")
        if status != 0:
            message = f"setNotifierName() returned {status}"
            #raise RuntimeError(message) # todo

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
                message = f"updateNotifierAlarm() returned {status}"
                #raise RuntimeError(message) # todo

            currentTimeUs, status = waitForNotifierAlarm(self._notifier)
            if status != 0:
                message = f"waitForNotifierAlarm() returned currentTimeUs={currentTimeUs} status={status}"
                #raise RuntimeError(message) # todo

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

    def _runCallbackAndReschedule(self, callback, currentTimeUs:int):
        callback.func()
        callback.setNextStartTimeUs(currentTimeUs)
        self._callbacks.add(callback)

    def endCompetition(self):
        stopNotifier(self._notifier)

    """
    todo this doesn't really translate to python (is it really needed?):    

    TimedRobot::~TimedRobot() {
      if (m_notifier != HAL_kInvalidHandle) {
        int32_t status = 0;
        HAL_StopNotifier(m_notifier, &status);
        FRC_ReportError(status, "StopNotifier");
      }
    }
    """

    def getLoopStartTime(self):
        return self.loopStartTimeUs/1e6  # todo units are seconds

    def addPeriodic(self,
                    callback,  # todo typehint
                    period: float,  # todo units seconds
                    offset: float = 0.0):  # todo units seconds
        self._callbacks.add(
            _Callback.makeCallBack(
                callback,
                self._startTimeUs, int(period * 1e6), int(offset * 1e6)
            )
        )
