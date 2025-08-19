import dataclasses
import tomlkit
import typing as T

from .util import parse_input


@dataclasses.dataclass
class SubprojectConfig:
    #: The key in `py_versions` to set the project version from
    py_version: str

    #: Whether this should be built for the robot platform or not
    robot: bool

    #: Whether `ci scan-headers` should include this project
    ci_scan_headers: bool = True

    ci_update_yaml: bool = True


@dataclasses.dataclass
class Parameters:
    wpilib_bin_version: str
    wpilib_bin_url: str

    exclude_artifacts: T.Set[str]

    requirements: T.Dict[str, str]

    robot_wheel_platform: str


@dataclasses.dataclass
class UpdateConfig:
    py_versions: T.Dict[str, str]
    params: Parameters
    subprojects: T.Dict[str, SubprojectConfig]


def load(fname) -> T.Tuple[UpdateConfig, tomlkit.TOMLDocument]:
    with open(fname) as fp:
        cfgdata = tomlkit.parse(fp.read())

    return parse_input(cfgdata, UpdateConfig, fname), cfgdata
