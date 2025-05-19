import contextlib
import pathlib
import subprocess
import sys
import sysconfig
import typing

import toposort

from . import config
from .subproject import Subproject
from .util import run_pip


class Context:
    """Global context used by all rdev commands"""

    def __init__(self, verbose: bool) -> None:
        self.verbose = verbose
        self.root_path = pathlib.Path(__file__).parent.parent
        self.subprojects_path = self.root_path / "subprojects"
        self.cfgpath = self.root_path / "rdev.toml"
        self.cfg, self.rawcfg = config.load(self.cfgpath)

        self.is_roborio = sysconfig.get_platform() == "linux-roborio"

        self.wheel_path = self.root_path / "dist"
        self.other_wheel_path = self.root_path / "dist-other"

        subprojects: typing.List[Subproject] = []
        for project, cfg in self.cfg.subprojects.items():
            # Skip projects that aren't compatible with roborio
            if self.is_roborio and not cfg.roborio:
                continue

            subprojects.append(Subproject(cfg, self.subprojects_path / project))

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
            run_pip(
                "install",
                *[str(req) for req in external],
            )

        if internal:
            run_pip(
                "install",
                "--no-index",
                "--find-links",
                str(self.wheel_path),
                "--find-links",
                str(self.other_wheel_path),
                *[str(req) for req in internal],
            )
