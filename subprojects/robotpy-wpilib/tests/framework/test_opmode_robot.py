import importlib
import pytest
import threading
from wpilib import simulation as wsim
from wpilib.opmoderobot import OpModeRobot, autonomous, teleop, utility
from wpilib import OpMode, RobotState, autonomous as top_level_autonomous
from hal import RobotMode
from wpiutil import Color


class MockOpMode(OpMode):
    def __init__(self):
        super().__init__()
        self.disabled_periodic_count = 0
        self.opmode_run_count = 0
        self.opmode_stop_count = 0

    def disabled_periodic(self):
        self.disabled_periodic_count += 1

    def opmode_run(self, opmode_id: int):
        self.opmode_run_count += 1

    def opmode_stop(self):
        self.opmode_stop_count += 1


class OneArgOpMode(OpMode):
    def __init__(self, robot):
        super().__init__()

    def opmode_run(self, opmode_id: int):
        pass

    def opmode_stop(self):
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
    RobotState.clear_opmodes()


def test_opmode_decorators_attach_metadata():
    @autonomous(group="Drive", description="Auto desc")
    class AutoMode(OpMode):
        pass

    metadata = AutoMode._wpilib_opmode_metadata
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


def test_opmode_decorator_allows_decorated_subclass():
    @autonomous
    class BaseMode(OpMode):
        pass

    @teleop
    class DerivedMode(BaseMode):
        pass

    assert "_wpilib_opmode_metadata" in BaseMode.__dict__
    assert "_wpilib_opmode_metadata" in DerivedMode.__dict__
    assert BaseMode._wpilib_opmode_metadata.mode == RobotMode.AUTONOMOUS
    assert DerivedMode._wpilib_opmode_metadata.mode == RobotMode.TELEOPERATED


def test_opmode_decorator_rejects_non_opmode_class_eagerly():
    with pytest.raises(TypeError, match="must inherit from OpMode"):

        @autonomous
        class NotAnOpMode:
            pass


def test_opmode_decorator_preserves_explicit_metadata():
    @utility(
        name="Arm Test",
        group="Mechanisms",
        description="tests arm",
        text_color=Color.WHITE,
        background_color=Color.BLACK,
    )
    class UtilityMode(OpMode):
        pass

    metadata = UtilityMode._wpilib_opmode_metadata
    assert metadata.name == "Arm Test"
    assert metadata.text_color == Color.WHITE
    assert metadata.background_color == Color.BLACK
    assert top_level_autonomous is autonomous


def test_add_opmode():
    class MyMockRobot(MockRobot):
        def __init__(self):
            super().__init__()
            self.add_opmode(
                MockOpMode,
                RobotMode.AUTONOMOUS,
                "NoArgOpMode-Auto",
                "Group",
                "Description",
                Color.WHITE,
                Color.BLACK,
            )
            self.add_opmode(
                OneArgOpMode,
                RobotMode.UTILITY,
                "OneArgOpMode-Utility",
                "Group",
                "Description",
                Color.WHITE,
                Color.BLACK,
            )
            self.add_opmode(MockOpMode, RobotMode.TELEOPERATED, "NoArgOpMode")
            self.add_opmode(OneArgOpMode, RobotMode.TELEOPERATED, "OneArgOpMode")
            self.publish_opmodes()

    robot = MyMockRobot()
    options = wsim.DriverStationSim.get_opmode_options()

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


def test_clear_opmodes():
    class MyMockRobot(MockRobot):
        def __init__(self):
            super().__init__()
            self.add_opmode(MockOpMode, RobotMode.TELEOPERATED, "NoArgOpMode")
            self.publish_opmodes()

    robot = MyMockRobot()
    robot.clear_opmodes()

    options = wsim.DriverStationSim.get_opmode_options()
    assert len(options) == 0


def test_remove_opmode():
    class MyMockRobot(MockRobot):
        def __init__(self):
            super().__init__()
            self.add_opmode(MockOpMode, RobotMode.TELEOPERATED, "NoArgOpMode")
            self.add_opmode(OneArgOpMode, RobotMode.TELEOPERATED, "OneArgOpMode")
            self.publish_opmodes()

    robot = MyMockRobot()
    robot.remove_opmode(RobotMode.TELEOPERATED, "NoArgOpMode")
    robot.publish_opmodes()

    options = wsim.DriverStationSim.get_opmode_options()
    assert len(options) == 1
    assert options[0].name == "OneArgOpMode"


@pytest.fixture
def periodic_robot_test_fixture():
    class MyMockRobot(MockRobot):
        def __init__(self):
            super().__init__()
            self.add_opmode(MockOpMode, RobotMode.TELEOPERATED, "NoArgOpMode")
            self.publish_opmodes()

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
    kPeriod = 0.020  # 20 ms

    robot = periodic_robot_test_fixture

    wsim.wait_for_program_start()

    # robot_periodic should be called regardless of state
    assert robot.periodic_count == 0

    # Time step to get periodic calls on 20 ms robot loop
    wsim.step_timing(kPeriod)
    assert robot.periodic_count == 1

    # Additional time steps should continue calling robot_periodic
    wsim.step_timing(kPeriod)
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

    options = wsim.DriverStationSim.get_opmode_options()
    assert {opt.name for opt in options} == {"DefaultAutoMode", "DefaultTeleMode"}


def test_opmode_robot_discovery_bypasses_publish_override(tmp_path, monkeypatch):
    pkg = tmp_path / "publishoverridebot"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "robot.py").write_text("""\
from wpilib.opmoderobot import OpModeRobot
class Robot(OpModeRobot):
    def __init__(self):
        super().__init__()
        self.initialized = True

    def publish_opmodes(self):
        assert self.initialized
""")
    (pkg / "drive_mode.py").write_text("""\
from wpilib import PeriodicOpMode
from wpilib.opmoderobot import teleop
@teleop
class DriveMode(PeriodicOpMode):
    pass
""")

    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module("publishoverridebot.robot")
    module.Robot()

    options = wsim.DriverStationSim.get_opmode_options()
    assert {opt.name for opt in options} == {"DriveMode"}


def test_opmode_robot_ignores_undecorated_subclass_of_decorated_opmode(
    tmp_path, monkeypatch
):
    pkg = tmp_path / "inheritedmetadatabot"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "robot.py").write_text("""\
from wpilib.opmoderobot import OpModeRobot
class Robot(OpModeRobot):
    def __init__(self):
        super().__init__()
""")
    (pkg / "drive_modes.py").write_text("""\
from wpilib import PeriodicOpMode
from wpilib.opmoderobot import teleop
@teleop
class BaseDriveMode(PeriodicOpMode):
    pass
class DerivedDriveMode(BaseDriveMode):
    pass
""")

    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module("inheritedmetadatabot.robot")
    module.Robot()

    options = wsim.DriverStationSim.get_opmode_options()
    assert {opt.name for opt in options} == {"BaseDriveMode"}


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
    nested = pkg / "support"
    nested.mkdir()
    (nested / "bad_auto.py").write_text("""\
from wpilib import PeriodicOpMode
from wpilib.opmoderobot import autonomous
raise RuntimeError('should not import nested module outside opmodes')
@autonomous
class BadAuto(PeriodicOpMode):
    pass
""")

    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module("safeimportbot.robot")
    module.Robot()

    options = wsim.DriverStationSim.get_opmode_options()
    assert {opt.name for opt in options} == {"DefaultAutoMode"}


def test_opmode_robot_discovers_opmodes_package_recursively(tmp_path, monkeypatch):
    pkg = tmp_path / "nestedopmodesbot"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "robot.py").write_text("""\
from wpilib.opmoderobot import OpModeRobot
class Robot(OpModeRobot):
    def __init__(self):
        super().__init__()
""")
    opmodes = pkg / "opmodes"
    opmodes.mkdir()
    (opmodes / "__init__.py").write_text("")
    (opmodes / "drive.py").write_text("""\
from wpilib import PeriodicOpMode
from wpilib.opmoderobot import teleop
@teleop
class DriveMode(PeriodicOpMode):
    pass
""")
    nested = opmodes / "test"
    nested.mkdir()
    (nested / "__init__.py").write_text("")
    (nested / "servo.py").write_text("""\
from wpilib import PeriodicOpMode
from wpilib.opmoderobot import utility
@utility
class ServoMode(PeriodicOpMode):
    pass
""")

    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module("nestedopmodesbot.robot")
    module.Robot()

    options = wsim.DriverStationSim.get_opmode_options()
    assert {opt.name for opt in options} == {"DriveMode", "ServoMode"}


def test_opmode_robot_fails_on_syntax_error_in_scan_tree(tmp_path, monkeypatch):
    pkg = tmp_path / "brokenbot"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "robot.py").write_text("""\
from wpilib.opmoderobot import OpModeRobot
class Robot(OpModeRobot):
    def __init__(self):
        super().__init__()
""")
    (pkg / "broken.py").write_text("def nope(:\n")

    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module("brokenbot.robot")

    with pytest.raises(RuntimeError, match="broken.py"):
        module.Robot()


def test_opmode_robot_fails_on_candidate_import_error(tmp_path, monkeypatch):
    pkg = tmp_path / "importbrokenbot"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "robot.py").write_text("""\
from wpilib.opmoderobot import OpModeRobot
class Robot(OpModeRobot):
    def __init__(self):
        super().__init__()
""")
    (pkg / "bad_auto.py").write_text("""\
from wpilib import PeriodicOpMode
from wpilib.opmoderobot import autonomous
raise RuntimeError('boom')
@autonomous
class BadAuto(PeriodicOpMode):
    pass
""")

    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module("importbrokenbot.robot")

    with pytest.raises(RuntimeError, match="bad_auto.py"):
        module.Robot()


def test_opmode_robot_rejects_duplicate_names_within_mode(tmp_path, monkeypatch):
    pkg = tmp_path / "duplicatebot"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "robot.py").write_text("""\
from wpilib.opmoderobot import OpModeRobot
class Robot(OpModeRobot):
    def __init__(self):
        super().__init__()
""")
    (pkg / "drive_modes.py").write_text("""\
from wpilib import PeriodicOpMode
from wpilib.opmoderobot import teleop
@teleop(name='Drive')
class DriveModeA(PeriodicOpMode):
    pass
@teleop(name='Drive')
class DriveModeB(PeriodicOpMode):
    pass
""")

    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module("duplicatebot.robot")

    with pytest.raises(ValueError, match="duplicate"):
        module.Robot()


def test_opmode_robot_rejects_decorated_non_opmode_class(tmp_path, monkeypatch):
    pkg = tmp_path / "typecheckbot"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "robot.py").write_text("""\
from wpilib.opmoderobot import OpModeRobot
class Robot(OpModeRobot):
    def __init__(self):
        super().__init__()
""")
    (pkg / "not_an_opmode.py").write_text("""\
from wpilib.opmoderobot import autonomous
@autonomous
class NotAnOpMode:
    pass
""")

    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module("typecheckbot.robot")

    with pytest.raises(RuntimeError, match="OpMode"):
        module.Robot()


def test_expansion_hub_style_project_discovers_split_opmodes(tmp_path, monkeypatch):
    pkg = tmp_path / "expansionhubsample"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "robot.py").write_text("""\
from wpilib.opmoderobot import OpModeRobot
class Robot(OpModeRobot):
    motor0 = None
    def __init__(self):
        super().__init__()
""")
    (pkg / "defaultautomode.py").write_text("""\
from wpilib import PeriodicOpMode
from wpilib.opmoderobot import autonomous
@autonomous
class DefaultAutoMode(PeriodicOpMode):
    def __init__(self, robot):
        self.robot = robot
""")
    (pkg / "defaulttelemode.py").write_text("""\
from wpilib import PeriodicOpMode
from wpilib.opmoderobot import teleop
@teleop
class DefaultTeleMode(PeriodicOpMode):
    def __init__(self, robot):
        self.robot = robot
""")

    monkeypatch.syspath_prepend(str(tmp_path))
    module = importlib.import_module("expansionhubsample.robot")
    module.Robot()

    options = wsim.DriverStationSim.get_opmode_options()
    assert {opt.name for opt in options} == {"DefaultAutoMode", "DefaultTeleMode"}
