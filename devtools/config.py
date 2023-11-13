import pydantic
import tomlkit
import typing


class Model(pydantic.BaseModel):
    class Config:
        extra = "forbid"


class SubprojectConfig(Model):
    #: If any managed project has one of these as a dependency, the
    #: minimum version should be this
    min_version: str

    #: Whether this should be built on roborio or not
    roborio: bool


class Parameters(Model):
    wpilib_bin_version: str
    wpilib_bin_url: str

    robotpy_build_req: str

    exclude_artifacts: typing.Set[str]

    parallel: typing.Optional[bool]
    cc_launcher: typing.Optional[str]
    strip_libpython: typing.Optional[bool]
    macosx_deployment_target: typing.Optional[str]


class UpdateConfig(Model):
    params: Parameters
    subprojects: typing.Dict[str, SubprojectConfig]


def load(fname) -> typing.Tuple[UpdateConfig, tomlkit.TOMLDocument]:
    with open(fname) as fp:
        cfgdata = tomlkit.parse(fp.read())

    return UpdateConfig(**cfgdata), cfgdata
