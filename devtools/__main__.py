import subprocess
import sys
import os
from pathlib import Path

try:
    import click
    import rich
    from .ctx import Context
    from . import ci
    from . import update_pyproject
    from .subproject import Subproject
    from .progress import progress
except (ImportError, ModuleNotFoundError):
    print("Installing robotpy dev requirements...")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "-r",
            (Path(__file__).parent.parent / "rdev_requirements.txt").resolve().as_posix(),
        ]
    )

    print("Try running the command again.")
    exit(0)



@click.group()
@click.option("--only", required=False, default=None, help="Only run for the specified project")
@click.option("--till", required=False, default=None, help="Only run until the specified project")
@click.pass_context
def main(ctx: click.Context, only: str, till: str):
    """RobotPy development tool"""
    obj = ctx.obj = Context()

    if obj.cfg.params.parallel is not None:
        os.environ.setdefault("RPYBUILD_PARALLEL", str(int(obj.cfg.params.parallel)))
    if obj.cfg.params.cc_launcher is not None:
        os.environ.setdefault("RPYBUILD_CC_LAUNCHER", obj.cfg.params.cc_launcher)
    if obj.cfg.params.strip_libpython is not None:
        os.environ.setdefault("RPYBUILD_STRIP_LIBPYTHON", str(int(obj.cfg.params.strip_libpython)))
    if obj.cfg.params.macosx_deployment_target is not None:
        os.environ.setdefault("MACOSX_DEPLOYMENT_TARGET", obj.cfg.params.macosx_deployment_target)

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "robotpy-build"+obj.cfg.params.robotpy_build_req,
        ],
        stdout=subprocess.DEVNULL,
    )

    if only is not None:
        obj.subprojects = {only: obj.subprojects[only]}
    elif till is not None:
        subprojects = {}
        for name, project in obj.subprojects.items():
            subprojects[name] = project
            if name == till:
                subprojects[name] = project
                break
        obj.subprojects = subprojects


main.add_command(ci.ci)
main.add_command(update_pyproject.update_pyproject)


@main.command()
@click.pass_obj
def info(ctx: Context):
    """Display information"""
    for project in progress(ctx.subprojects.values()):
        rich.print(project.name, ":", project.requires)


@main.command()
@click.pass_obj
def develop(ctx: Context):
    """Install all robotpy packages in editable mode"""
    for project in progress(ctx.subprojects.values()):
        project.develop()

@main.command()
@click.pass_obj
def build(ctx: Context):
    """Build all robotpy packages"""
    for project in progress(ctx.subprojects.values()):
        project.bdist_wheel(wheel_path=ctx.wheel_path, install=True)

@main.command()
@click.pass_obj
def test(ctx: Context):
    """Run all test scripts"""
    for project in progress(ctx.subprojects.values()):
        project.test()

@main.command()
@click.pass_obj
def clean(ctx: Context):
    """Clean all projects"""
    for project in progress(ctx.subprojects.values()):
        project.clean()

if __name__ == "__main__":
    main()