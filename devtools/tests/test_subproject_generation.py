import pathlib
from types import SimpleNamespace

from devtools.subproject import Subproject
from devtools.tests.test_pyproject_renderer import make_renderer


def make_subproject(tmp_path):
    renderer = make_renderer(tmp_path)
    rendered = renderer.render_all()["demo"]
    ctx = SimpleNamespace(
        run_pip=lambda *args, **kwargs: None,
        python="python",
        is_robot=False,
    )
    cfg = renderer.cfg.subprojects["demo"]
    project = Subproject(ctx, cfg, tmp_path / "subprojects" / "demo", rendered)
    return project, rendered


def test_subproject_uses_rendered_metadata_without_output(tmp_path):
    project, rendered = make_subproject(tmp_path)

    assert not rendered.output_path.exists()
    assert project.pyproject_name == "demo-pkg"
    assert str(project.build_requires[0]) == "hatch-robotpy~=0.2.1"


def test_develop_writes_only_its_project_before_pip(tmp_path):
    project, rendered = make_subproject(tmp_path)
    events = []
    original_write = rendered.write

    def write():
        events.append("write")
        return original_write()

    rendered.write = write
    project.ctx.run_pip = lambda *args, **kwargs: events.append("pip")

    project.develop("debug", None)

    assert events == ["write", "pip"]
    assert rendered.output_path.read_text() == rendered.text


def test_build_wheel_writes_before_build_frontend(tmp_path, monkeypatch):
    project, rendered = make_subproject(tmp_path)
    events = []
    original_write = rendered.write

    def write():
        events.append("write")
        return original_write()

    def fake_run_cmd(*args, **kwargs):
        events.append("build")
        outdir = pathlib.Path(args[args.index("--outdir") + 1])
        (outdir / "demo_pkg-2027.2.3-py3-none-any.whl").write_bytes(b"wheel")

    rendered.write = write
    monkeypatch.setattr("devtools.subproject.run_cmd", fake_run_cmd)
    monkeypatch.setattr(project, "_fix_wheel_name", lambda path: path.name)

    project.build_wheel(
        wheel_path=tmp_path / "dist",
        other_wheel_path=tmp_path / "dist-other",
        install=False,
        config_settings=[],
    )

    assert events == ["write", "build"]
