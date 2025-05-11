"""
Proof of concept to test TimedRobotPy using PyTest

This POC was made by deconstructing pytest_plugin.py so that it is no longer a plugin but a class that provides
fixtures.

To run / debug this:

pytest subprojects/robotpy-wpilib/tests/test_poc_timedrobot.py --no-header -vvv -s

"""

import pytest

from wpilib.timedrobotpy import TimedRobotPy


def run_practice(control: "TestController"):
    """Runs through the entire span of a practice match"""

    with control.run_robot():
        # Run disabled for a short period
        control.step_timing(seconds=0.5, autonomous=True, enabled=False)

        # Run autonomous + enabled for 15 seconds
        control.step_timing(seconds=15, autonomous=True, enabled=True)

        # Disabled for another short period
        control.step_timing(seconds=0.5, autonomous=False, enabled=False)

        # Run teleop + enabled for 2 minutes
        control.step_timing(seconds=120, autonomous=False, enabled=True)

class TestThings():

    class MyRobot(TimedRobotPy):
        def __init__(self):
            super().__init__(period=0.020)
            self.robotInitialized = False
            self.robotPeriodicCount = 0

        #########################################################
        ## Common init/update for all modes
        def robotInit(self):
            self.robotInitialized = True

        def robotPeriodic(self):
            self.robotPeriodicCount += 1
            print(f"in {self.__class__.__name__} periodic count={self.robotPeriodicCount}")

        #########################################################
        ## Autonomous-Specific init and update
        def autonomousInit(self):
            pass

        def autonomousPeriodic(self):
            pass

        def autonomousExit(self):
            pass

        #########################################################
        ## Teleop-Specific init and update
        def teleopInit(self):
            pass

        def teleopPeriodic(self):
            pass

        #########################################################
        ## Disabled-Specific init and update
        def disabledPeriodic(self):
            pass

        def disabledInit(self):
            pass

        #########################################################
        ## Test-Specific init and update
        def testInit(self):
            pass

        def testPeriodic(self):
            pass

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def myrobot_class(cls) -> type[MyRobot]:
        return cls.MyRobot

    @classmethod
    @pytest.fixture(scope="class", autouse=True)
    def robots_sim_enable_physics(cls) -> bool:
        return False


    def test_iterative(self, getTestController, robot_with_sim_setup_teardown):
        """Ensure that all states of the iterative robot run"""
        assert robot_with_sim_setup_teardown.robotInitialized == False
        assert robot_with_sim_setup_teardown.robotPeriodicCount == 0
        run_practice(getTestController)

        assert robot_with_sim_setup_teardown.robotInitialized == True
        assert robot_with_sim_setup_teardown.robotPeriodicCount > 0

    def test_iterative_again(self, getTestController, robot_with_sim_setup_teardown):
        """Ensure that all states of the iterative robot run"""
        assert robot_with_sim_setup_teardown.robotInitialized == False
        assert robot_with_sim_setup_teardown.robotPeriodicCount == 0
        run_practice(getTestController)

        assert robot_with_sim_setup_teardown.robotInitialized == True
        assert robot_with_sim_setup_teardown.robotPeriodicCount > 0
