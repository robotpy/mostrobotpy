from types import SimpleNamespace

from click.testing import CliRunner

from devtools.__main__ import update_pyproject
from devtools.ci import check_pyproject


class FakeRenderedProject:
    def __init__(self, changed):
        self.changed = changed
        self.calls = 0

    def write(self):
        self.calls += 1
        return self.changed


class FakeRenderer:
    def __init__(self, errors):
        self.errors = errors

    def validate_templates(self):
        return self.errors


def test_update_pyproject_writes_every_rendered_project():
    projects = {
        "one": FakeRenderedProject(True),
        "two": FakeRenderedProject(False),
    }
    ctx = SimpleNamespace(rendered_pyprojects=projects)

    result = CliRunner().invoke(update_pyproject, obj=ctx)

    assert result.exit_code == 0, result.output
    assert [project.calls for project in projects.values()] == [1, 1]
    assert "1 pyproject.toml file written" in result.output


def test_check_pyproject_reports_errors_without_writing():
    ctx = SimpleNamespace(
        pyproject_renderer=FakeRenderer(
            ["subprojects/demo/pyproject.in.toml: project.version is not neutral"]
        )
    )

    result = CliRunner().invoke(check_pyproject, obj=ctx)

    assert result.exit_code == 1
    assert "project.version is not neutral" in result.output


def test_check_pyproject_accepts_valid_templates():
    ctx = SimpleNamespace(pyproject_renderer=FakeRenderer([]))

    result = CliRunner().invoke(check_pyproject, obj=ctx)

    assert result.exit_code == 0, result.output
    assert "OK" in result.output
