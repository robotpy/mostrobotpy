import contextlib
import dataclasses
import pathlib
import typing as T

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
import tomlkit

from .config import UpdateConfig

NEUTRAL_VERSION = "0.0.0"
NEUTRAL_SPECIFIER = SpecifierSet("==0.0.0")


@contextlib.contextmanager
def _template_errors(path: pathlib.Path) -> T.Iterator[None]:
    try:
        yield
    except Exception as exc:
        if isinstance(exc, ValueError) and str(exc).startswith(f"{path}:"):
            raise
        raise ValueError(f"{path}: {exc}") from exc


@dataclasses.dataclass
class RenderedProject:
    template_path: pathlib.Path
    output_path: pathlib.Path
    data: tomlkit.TOMLDocument
    text: str

    def write(self) -> bool:
        try:
            current = self.output_path.read_text()
        except FileNotFoundError:
            current = None
        if current == self.text:
            return False
        self.output_path.write_text(self.text)
        return True


class PyprojectRenderer:
    def __init__(self, cfg: UpdateConfig, subprojects_path: pathlib.Path) -> None:
        self.cfg = cfg
        self.subprojects_path = subprojects_path
        self.template_paths = {
            name: subprojects_path / name / "pyproject.in.toml"
            for name in cfg.subprojects
        }

        self.package_names = {}
        for name in cfg.subprojects:
            path = self.template_paths[name]
            with _template_errors(path):
                data = self._parse(name)
                self.package_names[name] = data["project"]["name"]

        self.version_specs = {
            self.package_names[name]: SpecifierSet(
                f"=={cfg.py_versions[project_cfg.py_version]}"
            )
            for name, project_cfg in cfg.subprojects.items()
        }
        self.version_specs.update(
            (name, SpecifierSet(spec)) for name, spec in cfg.params.requirements.items()
        )

    def _parse(self, name: str) -> tomlkit.TOMLDocument:
        path = self.template_paths[name]
        with _template_errors(path):
            data = tomlkit.parse(path.read_text())
        return data

    def _render(self, name: str) -> RenderedProject:
        path = self.template_paths[name]
        with _template_errors(path):
            data = self._parse(name)
            project_cfg = self.cfg.subprojects[name]
            data["project"]["version"] = self.cfg.py_versions[project_cfg.py_version]

            for requirements in (
                data["build-system"]["requires"],
                data["project"]["dependencies"],
            ):
                for index, requirement_text in enumerate(list(requirements)):
                    if requirement_text.endswith("==THIS_VERSION"):
                        continue
                    requirement = Requirement(requirement_text)
                    specifier = self.version_specs.get(requirement.name)
                    if specifier is not None:
                        requirement.specifier = specifier
                        requirements[index] = str(requirement)

            entry_points = data["project"].get("entry-points")
            if entry_points is not None:
                for key in list(entry_points):
                    for prefix, replacement in self.cfg.params.entrypoints.items():
                        if key.startswith(prefix):
                            if key != replacement:
                                entry_points[replacement] = entry_points[key]
                                del entry_points[key]
                            break

            downloads = (
                data.get("tool", {})
                .get("hatch", {})
                .get("build", {})
                .get("hooks", {})
                .get("robotpy", {})
                .get("maven_lib_download", [])
            )
            for download in downloads:
                artifact = download["artifact_id"]
                if artifact in self.cfg.params.exclude_artifacts:
                    continue
                if artifact in self.cfg.params.mrclib_artifacts:
                    download["repo_url"] = self.cfg.params.mrclib_bin_url
                    download["version"] = self.cfg.params.mrclib_bin_version
                else:
                    download["repo_url"] = self.cfg.params.wpilib_bin_url
                    download["version"] = self.cfg.params.wpilib_bin_version

            semiwrap = data.get("tool", {}).get("semiwrap")
            if semiwrap is not None:
                name_transform = semiwrap.get("name_transform")
                if name_transform is None:
                    name_transform = tomlkit.table()
                    semiwrap["name_transform"] = name_transform
                name_transform["default"] = "snake_case"
                name_transform["enum_value"] = "CAPS_CASE"
                name_transform["known_words"] = list(self.cfg.params.known_words)

            text = tomlkit.dumps(data)
            return RenderedProject(path, path.parent / "pyproject.toml", data, text)

    def render_all(self) -> T.Dict[str, RenderedProject]:
        return {name: self._render(name) for name in self.cfg.subprojects}

    def validate_templates(self) -> T.List[str]:
        errors = []

        def check(path, field, actual, expected):
            if actual != expected:
                errors.append(f"{path}: {field} must be {expected!r}, got {actual!r}")

        for name, path in self.template_paths.items():
            with _template_errors(path):
                data = self._parse(name)
                check(
                    path,
                    "project.version",
                    data["project"].get("version"),
                    NEUTRAL_VERSION,
                )

                for field, requirements in (
                    ("build-system.requires", data["build-system"]["requires"]),
                    ("project.dependencies", data["project"]["dependencies"]),
                ):
                    for requirement_text in requirements:
                        if requirement_text.endswith("==THIS_VERSION"):
                            continue
                        requirement = Requirement(requirement_text)
                        if requirement.name in self.version_specs:
                            check(
                                path,
                                f"{field} {requirement.name} specifier",
                                requirement.specifier,
                                NEUTRAL_SPECIFIER,
                            )

                entry_points = data["project"].get("entry-points", {})
                for key in entry_points:
                    for prefix in self.cfg.params.entrypoints:
                        if key.startswith(prefix):
                            check(path, f"entry-point key {key}", key, prefix)
                            break

                downloads = (
                    data.get("tool", {})
                    .get("hatch", {})
                    .get("build", {})
                    .get("hooks", {})
                    .get("robotpy", {})
                    .get("maven_lib_download", [])
                )
                for download in downloads:
                    artifact = download["artifact_id"]
                    if artifact in self.cfg.params.exclude_artifacts:
                        continue
                    check(
                        path,
                        f"Maven artifact {artifact} repo_url",
                        download.get("repo_url"),
                        "",
                    )
                    check(
                        path,
                        f"Maven artifact {artifact} version",
                        download.get("version"),
                        NEUTRAL_VERSION,
                    )

                semiwrap = data.get("tool", {}).get("semiwrap")
                if semiwrap is not None:
                    name_transform = semiwrap.get("name_transform", {})
                    check(
                        path,
                        "tool.semiwrap.name_transform.known_words",
                        name_transform.get("known_words"),
                        [],
                    )

        return errors
