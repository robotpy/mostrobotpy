import os
import sys

import click

from .ctx import Context
from . import ci
from . import update_pyproject

#
# Environment variables for configuring the builds
#

# Always run robotpy-build in parallel
os.environ["RPYBUILD_PARALLEL"] = "1"

# MACOSX_DEPLOYMENT_TARGET is required for linking to WPILib
if sys.platform == "darwin":
    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "12"


@click.group()
@click.pass_context
def main(ctx: click.Context):
    """RobotPy development tool"""
    ctx.obj = Context()


main.add_command(ci.ci)
main.add_command(update_pyproject.update_pyproject)


@main.command()
@click.pass_obj
def info(ctx: Context):
    """Display information"""
    for project in ctx.subprojects.values():
        print(project.name, project.requires)


@main.command()
@click.pass_obj
def develop(ctx: Context):
    """Install all robotpy packages in editable mode"""
    for project in ctx.subprojects.values():
        project.develop()


@main.command()
@click.pass_obj
def test(ctx: Context):
    """Run all test scripts"""
    for project in ctx.subprojects.values():
        project.test()


if __name__ == "__main__":
    main()
