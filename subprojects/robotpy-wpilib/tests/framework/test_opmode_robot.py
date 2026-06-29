import pytest
import threading
from wpilib import simulation as wsim
from wpilib.opmoderobot import OpModeRobot
from wpilib import OpMode, RobotState
from hal import RobotMode
from wpiutil import Color


class MockOpMode(OpMode):
    def __init__(self):
        super().__init__()
        self.disabled_periodic_count = 0
        self.op_mode_run_count = 0
        self.op_mode_stop_count = 0

    def disabled_periodic(self):
        self.disabled_periodic_count += 1

    def op_mode_run(self, op_mode_id: int):
        self.op_mode_run_count += 1

    def op_mode_stop(self):
        self.op_mode_stop_count += 1


class OneArgOpMode(OpMode):
    def __init__(self, robot):
        super().__init__()

    def op_mode_run(self, op_mode_id: int):
        pass

    def op_mode_stop(self):
        pass


class MockRobot(OpModeRobot):
    def __init__(self):
        super().__init__()
        self.driver_station_connected_count = 0
        self.none_periodic_count = 0
        self.periodic_count = 0

    def driver_station_connected(self):
        self.driver_station_connected_count += 1

    def none_periodic(self):
        self.none_periodic_count += 1

    def robot_periodic(self):
        self.periodic_count += 1


@pytest.fixture(autouse=True)
def sim_timing_setup():
    wsim.pause_timing()
    wsim.set_program_started(False)
    yield
    wsim.resume_timing()
    RobotState.clear_op_modes()


def test_add_op_mode():
    class MyMockRobot(MockRobot):
        def __init__(self):
            super().__init__()
            self.add_op_mode(
                MockOpMode,
                RobotMode.AUTONOMOUS,
                "NoArgOpMode-Auto",
                "Group",
                "Description",
                Color.WHITE,
                Color.BLACK,
            )
            self.add_op_mode(
                OneArgOpMode,
                RobotMode.UTILITY,
                "OneArgOpMode-Utility",
                "Group",
                "Description",
                Color.WHITE,
                Color.BLACK,
            )
            self.add_op_mode(MockOpMode, RobotMode.TELEOPERATED, "NoArgOpMode")
            self.add_op_mode(OneArgOpMode, RobotMode.TELEOPERATED, "OneArgOpMode")
            self.publish_op_modes()

    robot = MyMockRobot()
    options = wsim.DriverStationSim.get_op_mode_options()

    assert len(options) == 4

    opt_map = {opt.name: opt for opt in options}

    auto_opt = opt_map["NoArgOpMode-Auto"]
    assert auto_opt.group == "Group"
    assert auto_opt.description == "Description"
    assert auto_opt.text_color == 0xFFFFFF
    assert auto_opt.background_color == 0x000000

    tele_opt = opt_map["NoArgOpMode"]
    assert tele_opt.group == ""
    assert tele_opt.description == ""
    assert tele_opt.text_color == -1
    assert tele_opt.background_color == -1


def test_clear_op_modes():
    class MyMockRobot(MockRobot):
        def __init__(self):
            super().__init__()
            self.add_op_mode(MockOpMode, RobotMode.TELEOPERATED, "NoArgOpMode")
            self.publish_op_modes()

    robot = MyMockRobot()
    robot.clear_op_modes()

    options = wsim.DriverStationSim.get_op_mode_options()
    assert len(options) == 0


def test_remove_op_mode():
    class MyMockRobot(MockRobot):
        def __init__(self):
            super().__init__()
            self.add_op_mode(MockOpMode, RobotMode.TELEOPERATED, "NoArgOpMode")
            self.add_op_mode(OneArgOpMode, RobotMode.TELEOPERATED, "OneArgOpMode")
            self.publish_op_modes()

    robot = MyMockRobot()
    robot.remove_op_mode(RobotMode.TELEOPERATED, "NoArgOpMode")
    robot.publish_op_modes()

    options = wsim.DriverStationSim.get_op_mode_options()
    assert len(options) == 1
    assert options[0].name == "OneArgOpMode"


@pytest.fixture
def periodic_robot_test_fixture():
    class MyMockRobot(MockRobot):
        def __init__(self):
            super().__init__()
            self.add_op_mode(MockOpMode, RobotMode.TELEOPERATED, "NoArgOpMode")
            self.publish_op_modes()

    robot = MyMockRobot()

    robot_thread = threading.Thread(target=robot.start_competition)
    robot_thread.start()

    yield robot

    robot.end_competition()
    robot_thread.join()


@pytest.mark.xfail(reason="wpilib bug")
def test_none_periodic(periodic_robot_test_fixture):
    robot = periodic_robot_test_fixture

    wsim.wait_for_program_start()

    # Time step to get periodic calls on 20 ms robot loop
    wsim.step_timing(0.110)

    assert robot.none_periodic_count == 5


def test_robot_periodic(periodic_robot_test_fixture):
    k_period = 0.020  # 20 ms

    robot = periodic_robot_test_fixture

    wsim.wait_for_program_start()

    # robot_periodic should be called regardless of state
    assert robot.periodic_count == 0

    # Time step to get periodic calls on 20 ms robot loop
    wsim.step_timing(k_period)
    assert robot.periodic_count == 1

    # Additional time steps should continue calling robot_periodic
    wsim.step_timing(k_period)
    assert robot.periodic_count == 2
