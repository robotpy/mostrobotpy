import pathlib
import shutil
import sys
import tempfile
import typing as T

from packaging.requirements import Requirement
import tomli

from .config import SubprojectConfig
from .util import run_cmd

if T.TYPE_CHECKING:
    from .ctx import Context


class Subproject:
    def __init__(
        self, ctx: "Context", cfg: SubprojectConfig, path: pathlib.Path
    ) -> None:
        self.ctx = ctx
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
        self.ctx.run_pip(
            "install",
            "-v",
            "-e",
            ".",
            "--no-build-isolation",
            "--config-settings=setup-args=-Dbuildtype=debug",
            cwd=self.path,
        )

    def uninstall(self):
        self.ctx.run_pip("uninstall", "-y", self.pyproject_name)

    def scan_headers(self):
        """Returns True if no headers found or False if missing headers were found"""
        result = run_cmd(
            self.ctx.python,
            "-m",
            "semiwrap",
            "scan-headers",
            "--check",
            cwd=self.path,
            check=False,
        )
        return result.returncode == 0

    def update_yaml(self):
        """Resyncs the yaml files with their header files"""
        result = run_cmd(
            self.ctx.python,
            "-m",
            "semiwrap",
            "update-yaml",
            "--write",
            cwd=self.path,
            check=False,
        )
        return result.returncode == 0

    def update_init(self):
        run_cmd(
            self.ctx.python,
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
                self.ctx.run_pip(
                    "install",
                    "-r",
                    str(requirements),
                )

        run_cmd(
            self.ctx.python,
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
                self.ctx.python,
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
            dst_whl = wheel_path / self._fix_wheel_name(twhl)
            shutil.move(twhl, dst_whl)
            print("Wrote wheel to", dst_whl)

        if install:
            # Install the wheel
            self.ctx.run_pip(
                "install",
                "--find-links",
                str(wheel_path),
                "--find-links",
                str(other_wheel_path),
                str(dst_whl),
            )

    _adjust_wheel_tags = {
        # needed for compatibility with python compiled with older xcode
        "macosx_11_0_x86_64": "macosx_10_16_x86_64",
        "macosx_12_0_x86_64": "macosx_10_16_x86_64",
    }

    def _fix_wheel_name(self, wheel_path: pathlib.Path) -> str:
        if sys.platform == "linux":
            name = self._fix_linux_wheel_name(wheel_path)
        else:
            name = wheel_path.name
            for old, new in self._adjust_wheel_tags.items():
                old_whl = f"{old}.whl"
                new_whl = f"{new}.whl"
                if name.endswith(old_whl):
                    name = f"{name[:-len(old_whl)]}{new_whl}"

        return name

    def _fix_linux_wheel_name(self, wheel_path: pathlib.Path) -> str:
        # inspired by https://github.com/hsorby/renamewheel, Apache license

        from auditwheel.error import NonPlatformWheel, WheelToolsError
        from auditwheel.wheel_abi import analyze_wheel_abi
        from auditwheel.wheeltools import get_wheel_architecture, get_wheel_libc

        try:
            arch = get_wheel_architecture(wheel_path.name)
        except (WheelToolsError, NonPlatformWheel):
            arch = None

        try:
            libc = get_wheel_libc(wheel_path.name)
        except WheelToolsError:
            libc = None

        try:
            winfo = analyze_wheel_abi(libc, arch, wheel_path, frozenset(), True, True)
        except NonPlatformWheel:
            return wheel_path.name
        else:
            parts = wheel_path.name.split("-")
            parts[-1] = winfo.overall_policy.name
            return "-".join(parts) + ".whl"
