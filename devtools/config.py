import dataclasses
import tomlkit

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

    mrclib_bin_version: str
    mrclib_bin_url: str
    mrclib_artifacts: set[str]

    #: semiwrap name_transform known_words shared by all wrapper projects
    known_words: list[str]

    #: renames [project.entry-points.KEY*] to [project.entry-points.VALUE]
    entrypoints: dict[str, str]

    exclude_artifacts: set[str]

    requirements: dict[str, str]

    robot_wheel_platform: str


@dataclasses.dataclass
class UpdateConfig:
    py_versions: dict[str, str]
    params: Parameters
    subprojects: dict[str, SubprojectConfig]


def load(fname) -> tuple[UpdateConfig, tomlkit.TOMLDocument]:
    with open(fname) as fp:
        cfgdata = tomlkit.parse(fp.read())

    return parse_input(cfgdata, UpdateConfig, fname), cfgdata
