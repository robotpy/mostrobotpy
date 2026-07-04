import os
import pathlib
import subprocess
import sys

import click

from .ctx import Context
from . import ci
from . import examples
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
main.add_command(examples.test_examples)
main.add_command(update_pyproject.update_pyproject)


@main.command()
@click.pass_obj
def info(ctx: Context):
    """Display information"""
    for project in ctx.subprojects.values():
        print(project.name, project.build_requires)


@main.command("regen-generated")
@click.pass_obj
def regen_generated(ctx: Context):
    """Regenerate checked-in generated files"""
    root = ctx.root_path
    hids_dir = root / "subprojects" / "robotpy-commands-v2" / "tools" / "hids"

    subprocess.run(
        [
            sys.executable,
            str(hids_dir / "generate_hids.py"),
            "--skip_hids",
            "--skip_first_ds_non_python",
            "--template_root",
            str(hids_dir / "templates"),
            "--first_ds_schema_file",
            str(hids_dir / "first_ds_hids.json"),
            "--python_output_directory",
            str(root / "subprojects" / "robotpy-commands-v2"),
        ],
        check=True,
    )


@main.command()
@click.argument("package", required=False)
@click.option("--test", default=False, is_flag=True)
@click.option(
    "--buildtype", default="debug", help="meson build type (debug, release, etc)"
)
@click.option(
    "--stop-at",
    metavar="PACKAGE",
    help="Build projects in normal order through PACKAGE, then stop",
)
@click.pass_obj
def develop(ctx: Context, package: str, test: bool, buildtype: str, stop_at: str):
    """Install robotpy packages in editable mode"""
    if stop_at and stop_at not in ctx.subprojects:
        raise click.BadParameter(f"invalid package {stop_at}", param_hint="--stop-at")

    if package:
        if stop_at:
            raise click.UsageError("--stop-at cannot be used when PACKAGE is specified")

        for project in ctx.subprojects.values():
            if project.name == package:
                project.develop(buildtype)
                if test:
                    project.test()
                break
        else:
            raise click.BadParameter(f"invalid package {package}")
    else:
        for project in ctx.subprojects.values():
            project.develop(buildtype)
            if test:
                project.test()
            if project.name == stop_at:
                break


@main.command()
@click.pass_obj
def install_prereqs(ctx: Context):
    """Install developer build dependencies before running develop"""

    reqs = set()
    reqs.add("editables")
    reqs.add("numpy")
    reqs.add("pytest")

    repo_deps = set()

    for project in ctx.subprojects.values():
        with ctx.handle_exception(project.name):
            repo_deps.add(project.pyproject_name)

            for req in project.build_requires + project.dependencies:
                if req.name not in repo_deps:
                    reqs.add(req)

    ctx.run_pip("install", *map(str, reqs))


@main.command()
@click.pass_obj
def scan_headers(ctx: Context):
    """Run scan-headers on all projects"""
    ok = True
    for project in ctx.subprojects.values():
        if project.is_semiwrap_project():
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
