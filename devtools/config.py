import dataclasses
import tomlkit
import typing as T

from .util import parse_input


@dataclasses.dataclass
class SubprojectConfig:
    
    #: Whether this should be built on roborio or not
    roborio: bool

    #: If any managed project has one of these as a dependency, the
    #: minimum version should be this
    min_version: T.Optional[str] = None


@dataclasses.dataclass
class Parameters:
    wpilib_bin_version: str
    wpilib_bin_url: str

    robotpy_build_req: str

    exclude_artifacts: T.Set[str]

    requirements: T.Dict[str, str]

@dataclasses.dataclass
class UpdateConfig:
    params: Parameters
    subprojects: T.Dict[str, SubprojectConfig]


def load(fname) -> T.Tuple[UpdateConfig, tomlkit.TOMLDocument]:
    with open(fname) as fp:
        cfgdata = tomlkit.parse(fp.read())

    return parse_input(cfgdata, UpdateConfig, fname), cfgdata
