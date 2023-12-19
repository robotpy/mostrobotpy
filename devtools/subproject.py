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
        self.pyproject_path = self.path / "pyproject.toml"
        self.name = path.name

        # Use tomli here because it's faster and we just need the data
        with open(self.pyproject_path, "rb") as fp:
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
            *[str(req) for req in self.requires],
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
            dst_whl = wheel_path / self._fix_wheel_name(twhl.name)
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

    _adjust_wheel_tags = {
        # pypi only accepts manylinux wheels, and we know we're compatible
        "linux_x86_64": "manylinux_2_35_x86_64",
        # needed for compatibility with python compiled with older xcode
        "macosx_11_0_x86_64": "macosx_10_16_x86_64",
        "macosx_12_0_x86_64": "macosx_10_16_x86_64",
    }

    def _fix_wheel_name(self, name: str) -> str:
        for old, new in self._adjust_wheel_tags.items():
            old_whl = f"{old}.whl"
            new_whl = f"{new}.whl"
            if name.endswith(old_whl):
                name = f"{name[:-len(old_whl)]}{new_whl}"
        return name
