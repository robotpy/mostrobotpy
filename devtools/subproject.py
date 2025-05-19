import pathlib
import shutil
import sys
import tempfile
import typing as T

from packaging.requirements import Requirement
import tomli

from .config import SubprojectConfig
from .util import run_cmd, run_pip


class Subproject:
    def __init__(self, cfg: SubprojectConfig, path: pathlib.Path) -> None:
        self.cfg = cfg
        self.path = path
        self.pyproject_path = self.path / "pyproject.toml"
        self.name = path.name

        # Use tomli here because it's faster and we just need the data
        with open(self.pyproject_path, "rb") as fp:
            self.pyproject_data = tomli.load(fp)

        self.build_requires = [
            Requirement(req) for req in self.pyproject_data["build-system"]["requires"]
        ]

        self.dependencies = [
            Requirement(req) for req in self.pyproject_data["project"]["dependencies"]
        ]

        self.pyproject_name: str = self.pyproject_data["project"]["name"]

    def is_semiwrap_project(self) -> bool:
        return self.pyproject_data.get("tool", {}).get("semiwrap", None) is not None

    def is_meson_project(self) -> bool:
        return (self.path / "meson.build").exists()

    #
    # Tasks
    #

    def develop(self):
        run_pip("install", "-v", "-e", ".", "--no-build-isolation", cwd=self.path)

    def uninstall(self):
        run_pip("uninstall", "-y", self.pyproject_name)

    def update_init(self):
        run_cmd(
            sys.executable,
            "-m",
            "semiwrap",
            "update-init",
            cwd=self.path,
        )

    def test(self, *, install_requirements=False):
        tests_path = self.path / "tests"
        if not tests_path.exists():
            return

        if install_requirements:
            requirements = tests_path / "requirements.txt"
            if requirements.exists():
                run_pip(
                    "install",
                    "-r",
                    str(requirements),
                )

        run_cmd(
            sys.executable,
            "run_tests.py",
            cwd=tests_path,
        )

    def build_wheel(
        self,
        *,
        wheel_path: pathlib.Path,
        other_wheel_path: pathlib.Path,
        install: bool,
        config_settings: T.List[str],
    ):
        wheel_path.mkdir(parents=True, exist_ok=True)

        config_args = [f"--config-setting={setting}" for setting in config_settings]

        # TODO: eventually it would be nice to use build isolation

        with tempfile.TemporaryDirectory() as td:
            # I wonder if we should use hatch build instead?
            run_cmd(
                sys.executable,
                "-m",
                "build",
                "--no-isolation",
                "--outdir",
                td,
                *config_args,
                cwd=self.path,
            )

            tdp = pathlib.Path(td)
            twhl = list(tdp.glob("*.whl"))[0]
            dst_whl = wheel_path / self._fix_wheel_name(twhl.name)
            shutil.move(twhl, dst_whl)

        if install:
            # Install the wheel
            run_pip(
                "install",
                "--find-links",
                str(wheel_path),
                "--find-links",
                str(other_wheel_path),
                str(dst_whl),
            )

    _adjust_wheel_tags = {
        # pypi only accepts manylinux wheels, and we know we're compatible
        # TODO(davo): use auditwheel to fix the tags instead
        "linux_x86_64": "manylinux_2_35_x86_64",
        "linux_aarch64": "manylinux_2_36_aarch64",
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
