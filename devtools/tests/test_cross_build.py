from pathlib import Path
import subprocess
from types import SimpleNamespace

from click.testing import CliRunner
import pytest

from devtools.cross_build import IMAGE, cross_build, snapshot


def test_snapshot_includes_edits_but_excludes_build_outputs(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / ".gitignore").write_text("ignored\n")
    (root / "tracked").write_text("original")
    (root / "deleted").write_text("gone")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    (root / "tracked").write_text("edited")
    (root / "deleted").unlink()
    for name in [
        "untracked",
        "ignored",
        "build/old",
        "build-actions/source",
        "wheels/old.whl",
    ]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(name)
    destination = tmp_path / "snapshot"
    snapshot(root, destination, root / "wheels")
    assert (destination / "tracked").read_text() == "edited"
    assert (destination / "untracked").read_text() == "untracked"
    assert {p.name for p in destination.iterdir()} == {
        "tracked",
        "untracked",
        ".gitignore",
    }


@pytest.mark.parametrize("failure", [False, True])
def test_export_only_after_success(monkeypatch, tmp_path, failure):
    root = tmp_path / "source"
    root.mkdir()
    output = tmp_path / "wheel output"
    output.mkdir()
    (output / "keep.txt").write_text("keep")
    monkeypatch.setattr("devtools.cross_build.shutil.which", lambda name: "/bin/docker")
    monkeypatch.setattr("devtools.cross_build.snapshot", lambda *args: None)

    def run(command, **kwargs):
        assert IMAGE in command
        assert command[-1] == "--buildtype=debug"
        assert "type=volume,source=rdev-systemcore-cache,target=/cache" in command
        mount = next(arg for arg in command if arg.endswith(",target=/export"))
        exported = Path(mount.split("source=", 1)[1].split(",target=", 1)[0])
        (exported / "demo.whl").write_bytes(b"wheel")
        if failure:
            raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr("devtools.cross_build.subprocess.run", run)
    result = CliRunner().invoke(
        cross_build,
        ["--output", str(output), "--buildtype", "debug"],
        obj=SimpleNamespace(root_path=root),
    )
    assert result.exit_code == (1 if failure else 0), result.output
    assert (output / "demo.whl").exists() is not failure
    assert (output / "keep.txt").read_text() == "keep"


def test_container_image_matches_ci():
    workflow = (Path(__file__).parents[2] / ".github/workflows/dist.yml").read_text()
    images = [
        line.split("container:", 1)[1].strip()
        for line in workflow.splitlines()
        if "- container:" in line
    ]
    assert images == [IMAGE, IMAGE]


def test_output_cannot_contain_sources(monkeypatch, tmp_path):
    monkeypatch.setattr("devtools.cross_build.shutil.which", lambda name: "/bin/docker")
    result = CliRunner().invoke(
        cross_build,
        ["--output", str(tmp_path)],
        obj=SimpleNamespace(root_path=tmp_path / "repo"),
    )
    assert result.exit_code == 2
    assert "must not contain" in result.output
