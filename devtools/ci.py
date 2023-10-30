#
# CI commands
#

import inspect
import pathlib
import typing

import click

from .ctx import Context


@click.group()
def ci():
    """CI commands"""


@ci.command()
@click.option("--no-test", default=False, is_flag=True)
@click.pass_obj
def run(ctx: Context, no_test: bool):
    """
    Builds wheels, runs tests
    """

    # TODO: Fix build dependencies to be == what we are building

    for project in ctx.subprojects.values():
        project.install_build_deps(wheel_path=ctx.wheel_path)
        project.bdist_wheel(wheel_path=ctx.wheel_path, install=True)
        if not no_test:
            project.test(install_requirements=True)
