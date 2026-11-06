"""Launch the CI cross build in an isolated Docker workspace."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import click

from .ctx import Context

IMAGE = "wpilib/systemcore-cross-debian:2026-trixie-py315"


def snapshot(root: Path, destination: Path, output: Path):
    """Copy current sources, including untracked edits, but no build artifacts."""
    paths = (
        subprocess.check_output(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=root,
        )
        .decode()
        .split("\0")
    )
    for name in set(paths) - {""}:
        relative = Path(name)
        if any(
            part
            in {"build-actions", "build", "dist", "dist-other", "cache", "__pycache__"}
            for part in relative.parts
        ):
            continue
        source = root / relative
        if source.resolve().is_relative_to(output) or not source.is_file():
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


@click.command("cross-build")
@click.option(
    "--output",
    required=True,
    type=click.Path(path_type=Path, file_okay=False),
    help="Destination for wheels (relative paths are relative to the repository).",
)
@click.option("--buildtype", help="Meson build type (release, debug, etc).")
@click.pass_obj
def cross_build(ctx: Context, output: Path, buildtype: str | None):
    """Build SystemCore wheels in CI's Docker image, with persistent ccache."""
    if shutil.which("docker") is None:
        raise click.ClickException("Docker is required for cross-build")
    output = output.resolve()
    root = ctx.root_path.resolve()
    if root.is_relative_to(output):
        raise click.BadParameter(
            "must not contain the source repository", param_hint="--output"
        )
    try:
        with tempfile.TemporaryDirectory(prefix="rdev-cross-") as temporary:
            staging = Path(temporary)
            source = staging / "source"
            exported = staging / "wheels"
            source.mkdir()
            exported.mkdir()
            snapshot(root, source, output)
            command = [
                "docker",
                "run",
                "--rm",
                "--platform",
                "linux/amd64",
                "--mount",
                f"type=bind,source={source},target=/source,readonly",
                "--mount",
                f"type=bind,source={exported},target=/export",
                "--mount",
                "type=volume,source=rdev-systemcore-cache,target=/cache",
                "--env",
                f"EXPORT_UID={os.getuid()}",
                "--env",
                f"EXPORT_GID={os.getgid()}",
                IMAGE,
                "bash",
                "/source/devtools/cross/local.sh",
            ]
            if buildtype:
                command.append(f"--buildtype={buildtype}")
            click.echo(f"Building in {IMAGE}")
            subprocess.run(command, check=True)
            wheels = list(exported.glob("*.whl"))
            if not wheels:
                raise click.ClickException("The build produced no wheels")
            output.mkdir(parents=True, exist_ok=True)
            for wheel in wheels:
                shutil.copy2(wheel, output / wheel.name)
            click.echo(f"Wrote {len(wheels)} wheels to {output}")
    except (OSError, subprocess.CalledProcessError) as exc:
        raise click.ClickException(str(exc)) from exc
