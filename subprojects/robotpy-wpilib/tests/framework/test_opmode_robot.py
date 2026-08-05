import importlib
import sys
import textwrap
import threading

import pytest
import wpilib
import wpilib._impl.opmode as opmode_impl
from wpilib import OpMode
from wpilib import simulation as wsim
from wpilib._wpilib import RobotState
from wpilib.opmoderobot import OpModeRobot, autonomous, teleop, utility
from hal import RobotMode
from wpiutil import Color


@pytest.fixture(autouse=True)
def reset_decorated_opmodes(monkeypatch):
    monkeypatch.setattr(opmode_impl, "_decorated_opmodes", [])
    RobotState.clear_opmodes()
    yield
    for module_name in tuple(sys.modules):
        if module_name == "samplebot" or module_name.startswith("samplebot."):
            sys.modules.pop(module_name)


def import_robot_package(monkeypatch, tmp_path, robot_source, module_contents):
    package_name = "samplebot"
    package_dir = tmp_path / package_name
    opmodes_dir = package_dir / "opmodes"
    opmodes_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("")
    (package_dir / "robot.py").write_text(textwrap.dedent(robot_source))
    (opmodes_dir / "__init__.py").write_text("")

    for relative_path, source in module_contents.items():
        module_path = package_dir / relative_path
        module_path.parent.mkdir(parents=True, exist_ok=True)
        module_path.write_text(textwrap.dedent(source))

    for module_name in tuple(sys.modules):
        if module_name == package_name or module_name.startswith(f"{package_name}."):
            sys.modules.pop(module_name)

    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()
    return package_dir, importlib.import_module(f"{package_name}.robot")


def test_opmode_decorators_attach_metadata():
    @autonomous(group="Drive", description="Auto desc")
    class AutoMode(OpMode):
        pass

    @teleop
    class TeleMode(OpMode):
        pass

    @utility(
        name="Arm Test",
        text_color=Color.WHITE,
        background_color=Color.BLACK,
    )
    class UtilityMode(OpMode):
        pass

    assert AutoMode._wpilib_opmode_metadata.mode == RobotMode.AUTONOMOUS
    assert AutoMode._wpilib_opmode_metadata.name == "AutoMode"
    assert AutoMode._wpilib_opmode_metadata.group == "Drive"
    assert AutoMode._wpilib_opmode_metadata.description == "Auto desc"
    assert TeleMode._wpilib_opmode_metadata.mode == RobotMode.TELEOPERATED
    assert TeleMode._wpilib_opmode_metadata.name == "TeleMode"
    assert UtilityMode._wpilib_opmode_metadata.mode == RobotMode.UTILITY
    assert UtilityMode._wpilib_opmode_metadata.name == "Arm Test"
    assert UtilityMode._wpilib_opmode_metadata.text_color == Color.WHITE
    assert UtilityMode._wpilib_opmode_metadata.background_color == Color.BLACK
    assert wpilib.autonomous is autonomous
    assert wpilib.teleop is teleop
    assert wpilib.utility is utility


def test_opmode_decorator_rejects_invalid_class_and_duplicate_mode():
    with pytest.raises(TypeError, match="OpMode subclass"):
        autonomous(type("NotAnOpMode", (), {}))

    @teleop
    class DriveMode(OpMode):
        pass

    with pytest.raises(ValueError, match="multiple opmode decorators"):
        autonomous(DriveMode)


def test_opmode_detector_recognizes_imported_module_alias():
    source = """
        from wpilib import PeriodicOpMode
        from wpilib import opmoderobot as modes

        @modes.utility
        class UtilityMode(PeriodicOpMode):
            pass
    """

    assert opmode_impl._has_opmode_decorator(textwrap.dedent(source), "utility.py")


def test_opmode_robot_auto_discovers_bounded_opmodes(monkeypatch, tmp_path):
    pkg, robot_module = import_robot_package(
        monkeypatch,
        tmp_path,
        """
        import wpilib as wpi

        class Robot(wpi.OpModeRobot):
            def __init__(self):
                super().__init__()
        """,
        {
            "opmodes/auto_mode.py": """
                import wpilib as wpi

                @wpi.autonomous(name="Auto")
                class AutoMode(wpi.PeriodicOpMode):
                    pass
            """,
            "opmodes/nested/__init__.py": "",
            "opmodes/nested/tele_mode.py": """
                from wpilib import PeriodicOpMode
                from wpilib.opmoderobot import teleop as tele

                @tele(group="Drive")
                class TeleMode(PeriodicOpMode):
                    pass
            """,
            "opmodes/ignored.py": """
                from pathlib import Path
                Path(__file__).with_name("ignored-imported").touch()
            """,
        },
    )

    robot_module.Robot()

    options = {
        option.name: option for option in wsim.DriverStationSim.get_opmode_options()
    }
    assert set(options) == {"Auto", "TeleMode"}
    assert options["TeleMode"].group == "Drive"
    assert not (pkg / "opmodes" / "ignored-imported").exists()


def test_opmode_robot_registers_explicitly_imported_decorated_opmode(
    monkeypatch, tmp_path
):
    _, robot_module = import_robot_package(
        monkeypatch,
        tmp_path,
        """
        import wpilib as wpi
        import samplebot.external_mode

        class Robot(wpi.OpModeRobot):
            def __init__(self):
                super().__init__()
        """,
        {
            "external_mode.py": """
                from wpilib import PeriodicOpMode
                from wpilib.opmoderobot import teleop

                @teleop
                class ImportedMode(PeriodicOpMode):
                    pass
            """,
        },
    )

    robot_module.Robot()

    options = wsim.DriverStationSim.get_opmode_options()
    assert [option.name for option in options] == ["ImportedMode"]


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
