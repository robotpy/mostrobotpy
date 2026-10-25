import os
import shlex
import sys
from types import MethodType

import pytest
from click.testing import CliRunner

from devtools import __main__ as cli
from devtools.ctx import Context
from devtools.tests.test_subproject_generation import make_subproject


@pytest.mark.parametrize("platform", ["linux", "darwin", "win32"])
@pytest.mark.parametrize("flags", [None, "-O1 -DUSER_FLAG=1"])
@pytest.mark.parametrize("args", [[], ["demo"], ["--stop-at", "demo"]])
@pytest.mark.parametrize(
    "option, setting, enabled",
    [
        ([], None, False),
        (["--portable-build-paths"], None, True),
        ([], "1", True),
        ([], "0", False),
        (["--no-portable-build-paths"], "1", False),
        (["--portable-build-paths"], "0", True),
    ],
)
def test_develop_portable_paths_are_opt_in(
    monkeypatch, tmp_path, platform, flags, args, option, setting, enabled
):
    project, _ = make_subproject(tmp_path / "checkout with spaces")
    ctx = project.ctx
    ctx.root_path = project.path.parent.parent
    ctx.subprojects = {project.name: project}
    ctx.python = sys.executable
    ctx.run_pip = MethodType(Context.run_pip, ctx)
    observed = []
    monkeypatch.setattr(
        "devtools.util.subprocess.run",
        lambda *args, **kwargs: observed.append(kwargs),
    )
    monkeypatch.setattr(cli.sys, "platform", platform)
    monkeypatch.setenv("CCACHE_BASEDIR", "/previous/base")
    monkeypatch.setenv("CCACHE_DIR", "/shared/cache")
    for name, value in [("CXXFLAGS", flags), ("RDEV_PORTABLE_BUILD_PATHS", setting)]:
        if value is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, value)
    original_env = dict(os.environ)

    result = CliRunner().invoke(cli.develop, [*option, *args], obj=ctx)

    assert result.exit_code == 0, result.output
    (call,) = observed
    assert dict(os.environ) == original_env
    if enabled:
        env = call["env"]
        assert env["CCACHE_DIR"] == "/shared/cache"
        assert env["PATH"] == original_env["PATH"]
        assert env["CCACHE_BASEDIR"] == str(ctx.root_path)
        assert shlex.split(env["CXXFLAGS"]) == [
            *shlex.split(flags or ""),
            f"-ffile-prefix-map={ctx.root_path}=.",
        ]
    else:
        assert call.get("env") is None
