import importlib
import pytest
import threading
from wpilib import simulation as wsim
from wpimath.units import seconds
from wpilib.opmoderobot import OpModeRobot, autonomous, teleop, utility
from wpilib import OpMode, RobotState, autonomous as top_level_autonomous
from hal._wpiHal import RobotMode
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

    def driverStationConnected(self):
        self.driver_station_connected_count += 1

    def nonePeriodic(self):
        self.none_periodic_count += 1

    def robotPeriodic(self):
        self.periodic_count += 1


@pytest.fixture(autouse=True)
def sim_timing_setup():
    wsim.pauseTiming()
    wsim.setProgramStarted(False)
    yield
    wsim.resumeTiming()
    RobotState.clearOpModes()


def test_opmode_decorators_attach_metadata():
    @autonomous(group="Drive", description="Auto desc")
    class AutoMode(OpMode):
        pass

    metadata = AutoMode.__wpilib_opmode_metadata__
    assert metadata.mode == RobotMode.AUTONOMOUS
    assert metadata.name == "AutoMode"
    assert metadata.group == "Drive"
    assert metadata.description == "Auto desc"


def test_opmode_decorator_rejects_multiple_modes():
    with pytest.raises(ValueError, match="multiple opmode decorators"):

        @teleop
        @autonomous
        class BadMode(OpMode):
            pass


def test_opmode_decorator_preserves_explicit_metadata():
    @utility(
        name="Arm Test",
        group="Mechanisms",
        description="tests arm",
        textColor=Color.WHITE,
        backgroundColor=Color.BLACK,
    )
    class UtilityMode(OpMode):
        pass

    metadata = UtilityMode.__wpilib_opmode_metadata__
    assert metadata.name == "Arm Test"
    assert metadata.textColor == Color.WHITE
    assert metadata.backgroundColor == Color.BLACK
    assert top_level_autonomous is autonomous


def test_add_op_mode():
    class MyMockRobot(MockRobot):
        def __init__(self):
            super().__init__()
            self.addOpMode(
                MockOpMode,
                RobotMode.AUTONOMOUS,
                "NoArgOpMode-Auto",
                "Group",
                "Description",
                Color.WHITE,
                Color.BLACK,
            )
            self.addOpMode(
                OneArgOpMode,
                RobotMode.UTILITY,
                "OneArgOpMode-Utility",
                "Group",
                "Description",
                Color.WHITE,
                Color.BLACK,
            )
            self.addOpMode(MockOpMode, RobotMode.TELEOPERATED, "NoArgOpMode")
            self.addOpMode(OneArgOpMode, RobotMode.TELEOPERATED, "OneArgOpMode")
            self.publishOpModes()

    robot = MyMockRobot()
    options = wsim.DriverStationSim.getOpModeOptions()

    assert len(options) == 4

    opt_map = {opt.name: opt for opt in options}

    auto_opt = opt_map["NoArgOpMode-Auto"]
    assert auto_opt.group == "Group"
    assert auto_opt.description == "Description"
    assert auto_opt.textColor == 0xFFFFFF
    assert auto_opt.backgroundColor == 0x000000

    tele_opt = opt_map["NoArgOpMode"]
    assert tele_opt.group == ""
    assert tele_opt.description == ""
    assert tele_opt.textColor == -1
    assert tele_opt.backgroundColor == -1


def test_clear_op_modes():
    class MyMockRobot(MockRobot):
        def __init__(self):
            super().__init__()
            self.addOpMode(MockOpMode, RobotMode.TELEOPERATED, "NoArgOpMode")
            self.publishOpModes()

    robot = MyMockRobot()
    robot.clearOpModes()

    options = wsim.DriverStationSim.getOpModeOptions()
    assert len(options) == 0


def test_remove_op_mode():
    class MyMockRobot(MockRobot):
        def __init__(self):
            super().__init__()
            self.addOpMode(MockOpMode, RobotMode.TELEOPERATED, "NoArgOpMode")
            self.addOpMode(OneArgOpMode, RobotMode.TELEOPERATED, "OneArgOpMode")
            self.publishOpModes()

    robot = MyMockRobot()
    robot.removeOpMode(RobotMode.TELEOPERATED, "NoArgOpMode")
    robot.publishOpModes()

    options = wsim.DriverStationSim.getOpModeOptions()
    assert len(options) == 1
    assert options[0].name == "OneArgOpMode"


@pytest.fixture
def periodic_robot_test_fixture():
    class MyMockRobot(MockRobot):
        def __init__(self):
            super().__init__()
            self.addOpMode(MockOpMode, RobotMode.TELEOPERATED, "NoArgOpMode")
            self.publishOpModes()

    robot = MyMockRobot()

    robot_thread = threading.Thread(target=robot.startCompetition)
    robot_thread.start()

    yield robot

    robot.endCompetition()
    robot_thread.join()


@pytest.mark.xfail(reason="wpilib bug")
def test_none_periodic(periodic_robot_test_fixture):
    robot = periodic_robot_test_fixture

    wsim.waitForProgramStart()

    # Time step to get periodic calls on 20 ms robot loop
    wsim.stepTiming(0.110)

    assert robot.none_periodic_count == 5


def test_robot_periodic(periodic_robot_test_fixture):
    kPeriod = 0.020  # 20 ms

    robot = periodic_robot_test_fixture

    wsim.waitForProgramStart()

    # RobotPeriodic should be called regardless of state
    assert robot.periodic_count == 0

    # Time step to get periodic calls on 20 ms robot loop
    wsim.stepTiming(kPeriod)
    assert robot.periodic_count == 1

    # Additional time steps should continue calling RobotPeriodic
    wsim.stepTiming(kPeriod)
    assert robot.periodic_count == 2


def test_opmode_robot_auto_discovers_decorated_modules(tmp_path, monkeypatch):
    pkg = tmp_path / "samplebot"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "robot.py").write_text("""\
from wpilib.opmoderobot import OpModeRobot
class Robot(OpModeRobot):
    def __init__(self):
        super().__init__()
""")
    (pkg / "default_auto_mode.py").write_text("""\
from wpilib import PeriodicOpMode
from wpilib.opmoderobot import autonomous
@autonomous
class DefaultAutoMode(PeriodicOpMode):
    pass
""")
    (pkg / "default_tele_mode.py").write_text("""\
from wpilib import PeriodicOpMode
from wpilib.opmoderobot import teleop
@teleop
class DefaultTeleMode(PeriodicOpMode):
    pass
""")

    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module("samplebot.robot")
    robot = module.Robot()

    options = wsim.DriverStationSim.getOpModeOptions()
    assert {opt.name for opt in options} == {"DefaultAutoMode", "DefaultTeleMode"}


def test_opmode_robot_skips_non_candidate_files(tmp_path, monkeypatch):
    pkg = tmp_path / "safeimportbot"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "robot.py").write_text("""\
from wpilib.opmoderobot import OpModeRobot
class Robot(OpModeRobot):
    def __init__(self):
        super().__init__()
""")
    (pkg / "default_auto_mode.py").write_text("""\
from wpilib import PeriodicOpMode
from wpilib.opmoderobot import autonomous
@autonomous
class DefaultAutoMode(PeriodicOpMode):
    pass
""")
    (pkg / "helper.py").write_text("raise RuntimeError('should not import')\n")

    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module("safeimportbot.robot")
    module.Robot()

    options = wsim.DriverStationSim.getOpModeOptions()
    assert {opt.name for opt in options} == {"DefaultAutoMode"}
