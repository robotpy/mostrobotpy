import dataclasses
import pathlib
import typing

import click
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version
import tomlkit

from .config import SubprojectConfig
from .ctx import Context


@dataclasses.dataclass
class ProjectInfo:
    pyproject_toml: pathlib.Path
    cfg: SubprojectConfig
    data: tomlkit.TOMLDocument
    changed: bool = False


class ProjectUpdater:
    """
    Updates pyproject.toml versions for robotpy-build projects
    """

    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx
        self.cfg = ctx.cfg

        self.commit_changes: typing.Set[str] = set()

        # The required versions for everything
        # - in theory projects could have different requirements, but in
        #   practice this is simpler and we haven't had issues
        self.version_specs: typing.Dict[str, SpecifierSet] = {}

        # load all the pyproject.toml using tomlkit so we can make changes
        # and retain all the comments
        self.subprojects: typing.Dict[str, ProjectInfo] = {}
        for name, project in self.ctx.subprojects.items():
            with open(project.pyproject_path, "r") as fp:
                data = tomlkit.load(fp)

            self.subprojects[name] = ProjectInfo(
                pyproject_toml=project.pyproject_path,
                data=data,
                cfg=self.cfg.subprojects[name],
            )

            version = self.cfg.py_versions[project.cfg.py_version]

            self.version_specs[project.pyproject_name] = SpecifierSet(f"=={version}")

        for name, spec in self.cfg.params.requirements.items():
            self.version_specs[name] = SpecifierSet(spec)

    @property
    def changed(self) -> bool:
        return len(self.commit_changes) > 0

    @property
    def wpilib_bin_version(self) -> str:
        return self.cfg.params.wpilib_bin_version

    @property
    def wpilib_bin_url(self) -> str:
        return self.cfg.params.wpilib_bin_url

    def _update_requirements(
        self,
        info: ProjectInfo,
        pypi_name: str,
        what: str,
        reqs: typing.List[str],
    ) -> bool:
        requires = list(reqs)
        changes = []
        for i, req_str in enumerate(requires):
            # special case
            if req_str.endswith("==THIS_VERSION"):
                continue

            req = Requirement(req_str)
            # see if the requirement is in our list of managed dependencies; if so
            # then change it if its different
            new_spec = self.version_specs.get(req.name)
            if new_spec is not None and new_spec != req.specifier:
                old_spec = str(req.specifier)
                req.specifier = new_spec
                reqs[i] = str(req)
                info.changed = True
                self.commit_changes.add(f"{what}: {req}")
                changes.append(f"{req.name}: '{old_spec}' => '{new_spec}'")

        if changes:
            print(f"* {pypi_name} {what}:")
            for change in changes:
                print("  -", change)
            return True

        return False

    def update_requirements(self):
        for info in self.subprojects.values():
            data = info.data
            pypi_name = data["project"]["name"]

            # update project.version
            self._update_pyversion(info)

            # update build-system
            self._update_requirements(
                info,
                pypi_name,
                "build-system.requires",
                data["build-system"]["requires"],
            )

            # project.dependencies
            self._update_requirements(
                info,
                pypi_name,
                "project.dependencies",
                data["project"]["dependencies"],
            )

    def _update_maven(self, info: ProjectInfo):
        data = info.data
        iter = (
            data["tool"]["hatch"]["build"]["hooks"]
            .get("robotpy", {})
            .get("maven_lib_download", [])
        )

        for dl in iter:

            if dl["artifact_id"] in self.cfg.params.exclude_artifacts:
                continue

            artifact_id = dl["artifact_id"]

            if dl["repo_url"] != self.wpilib_bin_url:
                print(
                    "* ",
                    artifact_id,
                    "repo url:",
                    dl["repo_url"],
                    "=>",
                    self.wpilib_bin_url,
                )
                self.commit_changes.add(f"repo updated to {self.wpilib_bin_url}")
                info.changed = True
                dl["repo_url"] = self.wpilib_bin_url

            if dl["version"] != self.wpilib_bin_version:
                print(
                    "* ",
                    artifact_id,
                    "so version:",
                    dl["version"],
                    "=>",
                    self.wpilib_bin_version,
                )
                self.commit_changes.add(f"lib updated to {self.wpilib_bin_version}")
                info.changed = True
                dl["version"] = self.wpilib_bin_version

    def update_maven(self):
        for data in self.subprojects.values():
            self._update_maven(data)

    def _update_pyversion(self, info: ProjectInfo):
        current_version = info.data["project"]["version"]
        version = self.cfg.py_versions[info.cfg.py_version]

        if current_version != version:
            name = info.data["project"]["name"]
            info.data["project"]["version"] = version
            print(f"* {name} {current_version!r} => {version!r}")
            self.commit_changes.add(f"{name} updated to {version}")
            info.changed = True

    def update(self):
        self.update_maven()
        self.update_requirements()

    def commit(self):
        files = []

        # check each file and fail if any are dirty
        for info in self.subprojects.values():
            if info.changed:
                if self.ctx.git_is_file_dirty(str(info.pyproject_toml)):
                    raise ValueError(f"{info.pyproject_toml} is dirty, aborting!")

        for info in self.subprojects.values():
            if info.changed:
                s = tomlkit.dumps(info.data)
                with open(info.pyproject_toml, "w") as fp:
                    fp.write(s)

                files.append(str(info.pyproject_toml))

        # Make a single useful commit with our changes
        msg = "Updated dependencies\n\n"
        msg += "- " + "\n- ".join(sorted(self.commit_changes))

        self.ctx.git_commit(msg, *files)


@click.command()
@click.option("--commit", default=False, is_flag=True)
@click.pass_obj
def update_pyproject(ctx: Context, commit: bool):
    """
    Updates pyproject.toml version requirements for all projects.

    It is expected that first the wpilib_bin_url and wpilib_bin_version
    are updated and pushed as a PR. If that succeeds, the PR is merged
    to main and then the min_version is updated for each project if
    needed. That commit should be pushed directly to main along with
    an appropriate tag.
    """

    # TODO: Make a bot or something to run this process automatically?

    if commit:
        print("Making changes...")
    else:
        print("Checking for changes...")

    updater = ProjectUpdater(ctx)
    updater.update()

    if not updater.changed:
        print(".. no changes found")
    elif commit:
        updater.commit()
        print("Changes committed")
    else:
        print("Use --commit to make changes")
