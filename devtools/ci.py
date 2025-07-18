#
# CI commands
#

import pathlib
import subprocess
import sys
import typing as T

import click
from packaging.requirements import Requirement
from packaging.version import Version

from .ctx import Context
from .update_pyproject import ProjectUpdater


@click.group()
def ci():
    """CI commands"""


@ci.command()
@click.pass_obj
def check_pyproject(ctx: Context):
    """
    Ensures that all pyproject.toml files are in sync with rdev.toml
    """
    print("Checking for changes..")
    updater = ProjectUpdater(ctx)
    updater.update()
    if updater.changed:
        print(
            "ERROR: please use ./rdev.sh update-pyproject to synchronize pyproject.toml and rdev.toml",
            file=sys.stderr,
        )
        exit(1)
    else:
        print("OK")


@ci.command
@click.pass_obj
def check_tag(ctx: Context):
    """
    Ensures that the current git tag matches the 'wrapper' version
    """
    wrapper_version = Version(ctx.cfg.py_versions["wrapper"])
    raw_git_version = subprocess.check_output(
        ["git", "describe", "--tags"], encoding="utf-8"
    )
    git_version = Version(raw_git_version.split("-", 1)[0])
    print("Wrapper version :", wrapper_version)
    print("Git version     :", git_version)

    if wrapper_version != git_version:
        print("ERROR: git tag does not match wrapper version")
        exit(1)
    else:
        print("OK")


@ci.command()
@click.option("--no-test", default=False, is_flag=True)
@click.pass_obj
def build_other_wheels(ctx: Context, no_test: bool):
    """
    Builds wheels that don't use meson, runs tests
    """

    for project in ctx.subprojects.values():
        if project.is_meson_project():
            continue

        with ctx.handle_exception(project.name):
            ctx.install_build_deps(subproject=project)

            project.build_wheel(
                wheel_path=ctx.wheel_path,
                other_wheel_path=ctx.other_wheel_path,
                install=True,
                config_settings=[],
            )
            if not no_test:
                project.test(install_requirements=True)


@ci.command()
@click.option("--no-test", default=False, is_flag=True)
@click.option(
    "--cross",
    help="meson cross.txt file (installed at ~/.local/share/meson/cross/FILENAME)",
)
@click.pass_obj
def build_meson_wheels(ctx: Context, no_test: bool, cross: T.Optional[str]):
    """
    Builds wheels that use meson, runs tests.

    Needs wheels that are in the non-meson builds
    """

    # Fix build dependencies to be == what we are building
    # - install_requires already has this via ==THIS_VERSION in robotpy-build
    # for project in ctx.subprojects.values():
    #     for i in range(len(project.build_requires)):
    #         req = project.build_requires[i]
    #         if req.name in ctx.subprojects:
    #             project.build_requires[i] = Requirement(f"{req.name}=={version}")

    # Check that the build dependencies match the versions of the projects
    # that we're building

    config_settings = []
    if cross:
        config_settings.append(f"setup-args=--cross-file={cross}")

    for project in ctx.subprojects.values():
        if not project.is_meson_project():
            continue

        with ctx.handle_exception(project.name):
            ctx.install_build_deps(subproject=project)
            project.build_wheel(
                wheel_path=ctx.wheel_path,
                other_wheel_path=ctx.other_wheel_path,
                install=True,
                config_settings=config_settings,
            )
            if not no_test:
                project.test(install_requirements=True)


@ci.command()
@click.pass_obj
def scan_headers(ctx: Context):
    """Run scan-headers on all projects"""
    ok = True
    for project in ctx.subprojects.values():
        if project.is_semiwrap_project():
            if not project.cfg.ci_scan_headers:
                print("- Skipping", project.name, file=sys.stderr)
                continue

            with ctx.handle_exception(f"scan-headers {project.name}"):
                if not project.scan_headers():
                    print(
                        "- ERROR:",
                        project.pyproject_path,
                        "does not wrap/ignore every header!",
                    )
                    ok = False

    if not ok:
        sys.exit(1)
