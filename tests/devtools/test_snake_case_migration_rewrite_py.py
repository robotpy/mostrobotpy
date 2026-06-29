from devtools.snake_case_migration.manifest import Manifest, Mapping
from devtools.snake_case_migration.rewrite_py import rewrite_python_source


def test_rewrite_definitions_calls_attrs_and_keywords():
    manifest = Manifest(
        mappings=[
            Mapping(kind="method", old="robotInit", new="robot_init", source="test"),
            Mapping(kind="method", old="getDefault", new="get_default", source="test"),
            Mapping(kind="method", old="setExpiration", new="set_expiration", source="test"),
            Mapping(kind="parameter", old="initialPose", new="initial_pose", source="test"),
        ]
    )
    source = '''\
import wpilib

class MyRobot(wpilib.TimedRobot):
    def robotInit(self):
        inst = wpilib.DriverStation.getDefault()
        self.drive.setExpiration(timeout=0.1)
        self.odometry.resetPosition(initialPose=self.pose)
'''
    assert rewrite_python_source(source, manifest) == '''\
import wpilib

class MyRobot(wpilib.TimedRobot):
    def robot_init(self):
        inst = wpilib.DriverStation.get_default()
        self.drive.set_expiration(timeout=0.1)
        self.odometry.resetPosition(initial_pose=self.pose)
'''


def test_rewrite_preserves_type_names_and_dunders():
    manifest = Manifest(
        mappings=[
            Mapping(kind="function", old="makeCommand", new="make_command", source="test"),
            Mapping(kind="method", old="__iter__", new="__iter__", source="test"),
        ]
    )
    source = '''\
class MyCommand:
    def __iter__(self):
        return iter(())

def makeCommand():
    return MyCommand()
'''
    assert rewrite_python_source(source, manifest) == '''\
class MyCommand:
    def __iter__(self):
        return iter(())

def make_command():
    return MyCommand()
'''
