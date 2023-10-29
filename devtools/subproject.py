import pathlib
import subprocess
import shlex
import shutil
import sys
import tempfile

from packaging.requirements import Requirement
import tomli

from .config import SubprojectConfig


class Subproject:
    def __init__(self, cfg: SubprojectConfig, path: pathlib.Path) -> None:
        self.cfg = cfg
        self.path = path
        self.name = path.name

        with open(self.path / "pyproject.toml", "rb") as fp:
            self.pyproject_data = tomli.load(fp)

        self.requires = [
            Requirement(req) for req in self.pyproject_data["build-system"]["requires"]
        ]

        self.pyproject_name: str = self.pyproject_data["tool"]["robotpy-build"][
            "metadata"
        ]["name"]

    #
    # Tasks
    #

    def _cmd(self, *args: str, cwd=None):
        print("+", shlex.join(args))
        subprocess.check_call(args, cwd=cwd)

    def install_build_deps(self, *, wheel_path: pathlib.Path):
        self._cmd(
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--find-links",
            str(wheel_path),
            *[str(req) for req in self.requires]
        )

    def develop(self):
        self._cmd(
            sys.executable,
            "setup.py",
            "develop",
            "-N",
            cwd=self.path,
        )

    def test(self, *, install_requirements=False):
        tests_path = self.path / "tests"
        if install_requirements:
            requirements = tests_path / "requirements.txt"
            if requirements.exists():
                self._cmd(
                    sys.executable,
                    "-m",
                    "pip",
                    "--disable-pip-version-check",
                    "install",
                    "-r",
                    str(requirements),
                )

        self._cmd(
            sys.executable,
            "run_tests.py",
            cwd=tests_path,
        )

    def bdist_wheel(self, *, wheel_path: pathlib.Path, install: bool):
        wheel_path.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as td:
            # Use bdist_wheel here instead of other solutions because it
            # allows using ccache
            self._cmd(
                sys.executable,
                "setup.py",
                "bdist_wheel",
                "-d",
                td,
                cwd=self.path,
            )

            tdp = pathlib.Path(td)
            twhl = list(tdp.glob("*.whl"))[0]
            dst_whl = wheel_path / twhl.name
            shutil.move(twhl, dst_whl)

        # Setuptools is dumb
        for p in self.path.glob("*.egg-info"):
            shutil.rmtree(p)

        if install:
            # Install the wheel
            self._cmd(
                sys.executable,
                "-m",
                "pip",
                "--disable-pip-version-check",
                "install",
                "--force-reinstall",
                "--find-links",
                str(wheel_path),
                str(dst_whl),
            )
