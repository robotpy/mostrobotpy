import os
import pathlib
import sys

import click

from .ctx import Context
from . import ci
from . import update_pyproject

#
# Environment variables for configuring the builds
#

# cache downloaded files by default
if "HATCH_ROBOTPY_CACHE" not in os.environ:
    os.environ["HATCH_ROBOTPY_CACHE"] = str(
        (pathlib.Path(__file__).parent.parent / "cache").resolve()
    )


# MACOSX_DEPLOYMENT_TARGET is required for linking to WPILib
if sys.platform == "darwin":
    os.environ["MACOSX_DEPLOYMENT_TARGET"] = "13.3"


@click.group()
@click.option("-v", "--verbose", default=False, is_flag=True)
@click.pass_context
def main(ctx: click.Context, verbose: bool):
    """RobotPy development tool"""
    ctx.obj = Context(verbose)


main.add_command(ci.ci)
main.add_command(update_pyproject.update_pyproject)


@main.command()
@click.pass_obj
def info(ctx: Context):
    """Display information"""
    for project in ctx.subprojects.values():
        print(project.name, project.build_requires)


@main.command()
@click.argument("package", required=False)
@click.pass_obj
def develop(ctx: Context, package: str):
    """Install robotpy packages in editable mode"""
    if package:
        for project in ctx.subprojects.values():
            if project.name == package:
                project.develop()
                break
        else:
            raise click.BadParameter(f"invalid package {package}")
    else:
        for project in ctx.subprojects.values():
            project.develop()


@main.command
@click.argument("package", required=False)
@click.pass_obj
def uninstall(ctx: Context, package: str):
    """Uninstall robotpy packages"""
    if package:
        for project in ctx.subprojects.values():
            if project.name == package:
                project.uninstall()
                break
        else:
            raise click.BadParameter(f"invalid package {package}")
    else:
        for project in ctx.subprojects.values():
            project.uninstall()


@main.command()
@click.pass_obj
def update_init(ctx: Context):
    """Update __init__.py in all projects"""
    for project in ctx.subprojects.values():
        if project.is_semiwrap_project():
            with ctx.handle_exception(f"update-init {project.name}"):
                project.update_init()


@main.command()
@click.pass_obj
def test(ctx: Context):
    """Run all test scripts"""
    for project in ctx.subprojects.values():
        project.test()


if __name__ == "__main__":
    main()
