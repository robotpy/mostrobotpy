import subprocess
import sys
from pathlib import Path

from devtools.snake_case_migration.manifest import Manifest, Mapping, save_manifest
from devtools.snake_case_migration.rewrite_py import rewrite_python_source


def test_rewrite_py_cli_rewrites_file(tmp_path: Path):
    manifest_path = tmp_path / "manifest.toml"
    source_path = tmp_path / "robot.py"
    save_manifest(
        manifest_path,
        Manifest(
            mappings=[
                Mapping(kind="method", old="robotInit", new="robot_init", source="test")
            ]
        ),
    )
    source_path.write_text("def robotInit():\n    pass\n")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "devtools.snake_case_migration",
            "--manifest",
            str(manifest_path),
            "rewrite-py",
            "--write",
            str(source_path),
        ],
        check=True,
    )
    assert source_path.read_text() == "def robot_init():\n    pass\n"


def test_rewrite_definitions_calls_attrs_and_keywords():
    manifest = Manifest(
        mappings=[
            Mapping(kind="method", old="robotInit", new="robot_init", source="test"),
            Mapping(kind="method", old="getDefault", new="get_default", source="test"),
            Mapping(
                kind="method", old="GetFPGATime", new="get_fpga_time", source="test"
            ),
            Mapping(
                kind="method", old="setExpiration", new="set_expiration", source="test"
            ),
            Mapping(
                kind="parameter", old="initialPose", new="initial_pose", source="test"
            ),
        ]
    )
    source = """\
import wpilib

class MyRobot(wpilib.TimedRobot):
    def robotInit(self):
        inst = wpilib.DriverStation.getDefault()
        timestamp = wpilib.Timer.GetFPGATime()
        self.drive.setExpiration(timeout=0.1)
        self.odometry.resetPosition(initialPose=self.pose)
"""
    assert rewrite_python_source(source, manifest) == """\
import wpilib

class MyRobot(wpilib.TimedRobot):
    def robot_init(self):
        inst = wpilib.DriverStation.get_default()
        timestamp = wpilib.Timer.get_fpga_time()
        self.drive.set_expiration(timeout=0.1)
        self.odometry.resetPosition(initial_pose=self.pose)
"""


def test_rewrite_preserves_type_names_and_dunders():
    manifest = Manifest(
        mappings=[
            Mapping(
                kind="function", old="makeCommand", new="make_command", source="test"
            ),
            Mapping(kind="class", old="MyCommand", new="my_command", source="test"),
            Mapping(kind="method", old="__iter__", new="iter", source="test"),
        ]
    )
    source = """\
class MyCommand:
    def __iter__(self):
        return iter(())

def makeCommand():
    return MyCommand()
"""
    assert rewrite_python_source(source, manifest) == """\
class MyCommand:
    def __iter__(self):
        return iter(())

def make_command():
    return MyCommand()
"""
