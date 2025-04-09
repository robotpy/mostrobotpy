from heapq import heappush, heappop
import hal

from hal import report, initializeNotifier, setNotifierName, observeUserProgramStarting, updateNotifierAlarm, \
    waitForNotifierAlarm
from wpilib import RobotController

from wpilib.iterativerobotpy import IterativeRobotPy


class Callback:
    def __init__(self, func, periodUs: int, expirationUs: int):
        self.func = func
        self.periodUs = periodUs
        self.expirationUs = expirationUs

    @classmethod
    def makeCallBack(cls,
                     func,
                     startTimeUs: int,
                     periodUs: int,
                     offsetUs: int):
        # todo does the "// periodUs * periodUs" do the correct integer math?
        nowUs = RobotController.getFPGATime()
        #print(f"makeCallBack getFPGATim={nowUs}")
        expirationUs = \
            startTimeUs + offsetUs + periodUs + \
            ((nowUs - startTimeUs) // periodUs) * periodUs

        return Callback(
            func,
            periodUs,
            expirationUs
        )

    def setNextExpirationTimeDelta(self, currentTimeUs: int):
        # increment the expiration time by the number of full periods it's behind
        # plus one to avoid rapid repeat fires from a large loop overrun. We assume
        # currentTime ≥ expirationTime rather than checking for it since the
        # callback wouldn't be running otherwise.
        # todo does this math work?
        self.expirationUs = self.expirationUs + self.periodUs \
            + ((currentTimeUs - self.expirationUs)  // self.periodUs) * self.periodUs

    def __lt__(self, other):
        return self.expirationUs < other.expirationUs

    def __bool__(self):
        return True


class OrderedList:
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

    def __init__(self, periodS: float = 0.020):  # todo are the units on period correct?
        super().__init__(periodS)

        self.startTimeUs = RobotController.getFPGATime()
        #print(f"self.startTimeUs={int(self.startTimeUs/timedelta(microseconds=1))}")
        self.callbacks = OrderedList()
        self.addPeriodic(self.loopFunc, period=periodS)

        self.notifier, status = initializeNotifier()
        #print(f"Initialized status={status} notifier={self.notifier}", flush=True)
        if status != 1:
            message = f"initializeNotifier() returned {status} {self.notifier}"
            raise RuntimeError(message)

        status = setNotifierName(self.notifier, "TimedRobot")
        if status != 1:
            raise RuntimeError(f"setNotifierName() returned {status}")

        report(hal.tResourceType.kResourceType_Framework, hal.tInstances.kFramework_Timed)

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
            #  there's always at least one (the constructor adds one). It's reenqueued
            #  at the end of the loop.
            callback = self.callbacks.pop()

            #print(f"type(callback)={type(callback)} type(callback.expirationUs)={type(callback.expirationUs)} callback.expirationUs={callback.expirationUs}", flush=True)

            timeout = callback.expirationUs
            fpgaTime = RobotController.getFPGATime()
            #print(f"timeout={timeout} fpgatime={fpgaTime}", flush=True)
            status = updateNotifierAlarm(self.notifier, timeout)
            #print(f"updateNotifierAlarm({self.notifier}, {timeout}) status={status}", flush=True)
            #if status != 0:
            #    message = f"updateNotifierAlarm() returned {status}"
            #    print(message, flush=True)
            #    raise RuntimeError(message)

            currentTimeUs, status = waitForNotifierAlarm(self.notifier)  # todo what are the return values, what is the return order?
            if status != 0:
                message = f"waitForNotifierAlarm() returned currentTimeUs={currentTimeUs} status={status}"
                #print(message, flush=True)
                #raise RuntimeError(message)

            if currentTimeUs == 0:
                break
            self.loopStartTimeUs = RobotController.getFPGATime()
            #print(f"self.loopStartTimeUs={self.loopStartTimeUs}")
            self._runCallbackAndReschedule(callback, currentTimeUs)

            #  Process all other callbacks that are ready to run
            while self.callbacks.peek().expirationUs <= currentTimeUs:
                callback = self.callbacks.pop()
                self._runCallbackAndReschedule(callback, currentTimeUs)

    def _runCallbackAndReschedule(self, callback, currentTimeUs):
        callback.func()
        callback.setNextExpirationTimeDelta(currentTimeUs)
        self.callbacks.add(callback)

    def endCompetition(self):
        hal.stopNotifier(self.notifier)

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
        self.callbacks.add(
            Callback.makeCallBack(
                callback,
                self.startTimeUs, int(period*1e6), int(offset*1e6)
            )
        )
