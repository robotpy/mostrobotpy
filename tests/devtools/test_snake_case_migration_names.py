import subprocess
import sys

from devtools.snake_case_migration.names import (
    DEFAULT_ACRONYMS,
    is_probably_type_name,
    to_caps_case,
    to_snake_case,
)


def test_snake_case_uses_wpilib_acronyms():
    assert "FPGA" in DEFAULT_ACRONYMS
    assert "OpMode" in DEFAULT_ACRONYMS
    assert to_snake_case("GetFPGATime") == "get_fpga_time"
    assert to_snake_case("isDSAttached") == "is_ds_attached"
    assert to_snake_case("toJSON") == "to_json"
    assert to_snake_case("getI2CHandle") == "get_i2c_handle"
    assert to_snake_case("GetOpMode") == "get_opmode"
    assert to_snake_case("OpModeOption") == "opmode_option"
    assert to_snake_case("PublishOpModes") == "publish_opmodes"


def test_controller_button_acronyms_keep_letters_and_numbers_together():
    assert to_snake_case("GetL1Button") == "get_l1_button"
    assert to_snake_case("L2Axis") == "l2_axis"
    assert to_snake_case("getR3") == "get_r3"
    assert to_caps_case("L1") == "L1"
    assert to_caps_case("R2") == "R2"


def test_caps_case_uses_wpilib_acronyms():
    assert to_caps_case("kHTTPServer") == "K_HTTP_SERVER"
    assert to_caps_case("valueOne") == "VALUE_ONE"


def test_name_transforms_preserve_leading_underscores():
    assert to_snake_case("_now") == "_now"
    assert to_snake_case("_GetFPGATime") == "_get_fpga_time"
    assert to_snake_case("__privateName") == "__private_name"
    assert to_caps_case("_kValue") == "_K_VALUE"


def test_type_name_detection_keeps_pascal_case_types():
    assert is_probably_type_name("TimedRobot") is True
    assert is_probably_type_name("NetworkTableInstance") is True
    assert is_probably_type_name("getDefault") is False
    assert is_probably_type_name("robotInit") is False


def test_cli_help_runs():
    result = subprocess.run(
        [sys.executable, "-m", "devtools.snake_case_migration", "--help"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert "snake_case_migration" in result.stdout
    assert "manifest" in result.stdout
    assert "rewrite-py" in result.stdout
