import contextlib
import pathlib
import subprocess
import sys
import sysconfig
import typing as T

import toposort

from . import config
from .subproject import Subproject
from .util import run_cmd


class Context:
    """Global context used by all rdev commands"""

    def __init__(self, verbose: bool) -> None:
        self.verbose = verbose
        self.root_path = pathlib.Path(__file__).parent.parent
        self.subprojects_path = self.root_path / "subprojects"
        self.cfgpath = self.root_path / "rdev.toml"
        self.cfg, self.rawcfg = config.load(self.cfgpath)

        self.is_robot = sysconfig.get_platform() == self.cfg.params.robot_wheel_platform

        self.wheel_path = self.root_path / "dist"
        self.other_wheel_path = self.root_path / "dist-other"

        subprojects: T.List[Subproject] = []
        for project, cfg in self.cfg.subprojects.items():
            # Skip projects that aren't compatible with the robot
            if self.is_robot and not cfg.robot:
                continue

            subprojects.append(Subproject(self, cfg, self.subprojects_path / project))

        # Create a sorted dictionary of subprojects ordered by build order
        si = {p.pyproject_name: i for i, p in enumerate(subprojects)}
        ti = {
            i: [si[r.name] for r in p.build_requires + p.dependencies if r.name in si]
            for i, p in enumerate(subprojects)
        }

        self.subprojects = {
            subprojects[i].name: subprojects[i]
            for i in toposort.toposort_flatten(ti, sort=False)
        }

        # build_python is for build dependencies, python is for the target environment
        # - if crossenv is specified, then we use that instead
        self._build_python = None
        self.python = sys.executable

    @property
    def build_python(self):
        if self._build_python is None:
            self._build_python = self.python

            # try to detect if we're running in crossenv's cross python and
            # use the build python instead
            if getattr(sys, "cross_compiling", False) == True:
                pth = pathlib.Path(self._build_python).resolve()
                if pth.parts[-3:-1] == ("cross", "bin"):
                    self._build_python = str(
                        pathlib.Path(
                            *(pth.parts[:-3] + ("build", "bin", pth.parts[-1]))
                        )
                    )

        return self._build_python

    def git_commit(self, msg: str, *relpath: str):
        subprocess.run(
            ["git", "commit", "-F", "-", "--"] + list(relpath),
            check=True,
            cwd=self.root_path,
            input=msg,
            text=True,
        )
        subprocess.run(
            ["git", "--no-pager", "log", "-1", "--stat"],
            check=True,
            cwd=self.root_path,
        )

    def git_is_file_dirty(self, relpath: str) -> bool:
        output = subprocess.check_output(
            ["git", "status", "--porcelain", relpath], cwd=self.root_path
        ).decode("utf-8")
        return output != ""

    @contextlib.contextmanager
    def handle_exception(self, msg: str):
        try:
            yield
        except Exception as e:
            if self.verbose:
                raise

            print(f"ERROR: {msg}: {e}", file=sys.stderr)
            sys.exit(1)

    @property
    def internal_pyprojects(self):
        if not hasattr(self, "_internal_pyprojects"):
            self._internal_pyprojects = [
                s.pyproject_name for s in self.subprojects.values()
            ]
        return self._internal_pyprojects

    def install_build_deps(
        self,
        *,
        subproject: Subproject,
    ):
        # separate requirements into internal and external
        internal = []
        external = []

        for req in subproject.build_requires:
            if req.name in self.internal_pyprojects:
                internal.append(req)
            else:
                external.append(req)

        if external:
            self.run_pip(
                "install",
                *[str(req) for req in external],
                installing_build_deps=True,
            )

        if internal:
            self.run_pip(
                "install",
                "--no-index",
                "--find-links",
                str(self.wheel_path),
                "--find-links",
                str(self.other_wheel_path),
                *[str(req) for req in internal],
            )

    def run_pip(self, *args: str, cwd=None, installing_build_deps: bool = False):
        if installing_build_deps:
            python = self.build_python
        else:
            python = self.python

        run_cmd(python, "-m", "pip", "--disable-pip-version-check", *args, cwd=cwd)
