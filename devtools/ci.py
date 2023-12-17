#
# CI commands
#

import sys

import click
from packaging.requirements import Requirement
import setuptools_scm

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


@ci.command()
@click.option("--no-test", default=False, is_flag=True)
@click.pass_obj
def run(ctx: Context, no_test: bool):
    """
    Builds wheels, runs tests
    """

    # Get the current build version
    version = setuptools_scm.get_version()

    # Fix build dependencies to be == what we are building
    # - install_requires already has this via ==THIS_VERSION in robotpy-build
    for project in ctx.subprojects.values():
        for i in range(len(project.requires)):
            req = project.requires[i]
            if req.name in ctx.subprojects:
                project.requires[i] = Requirement(f"{req.name}=={version}")

    for project in ctx.subprojects.values():
        project.install_build_deps(wheel_path=ctx.wheel_path)
        project.bdist_wheel(wheel_path=ctx.wheel_path, install=True)
        if not no_test:
            project.test(install_requirements=True)
