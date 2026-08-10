import os
import pathlib
from types import SimpleNamespace

import pytest
from packaging.requirements import InvalidRequirement

from devtools.pyproject import PyprojectRenderer

TEMPLATE = """\
[build-system]
requires = ["hatch-robotpy==0.0.0"]
build-backend = "hatchling.build"

[project]
name = "demo-pkg"
version = "0.0.0"
dependencies = ["other-pkg==0.0.0; python_version >= '3.10'"]

[project.entry-points.robotpy_sim]
run = "demo:main"

[[tool.hatch.build.hooks.robotpy.maven_lib_download]]
artifact_id = "wpilibc"
repo_url = ""
version = "0.0.0"

[tool.semiwrap.name_transform]
default = "snake_case"
enum_value = "CAPS_CASE"
known_words = []
"""


def make_renderer(
    tmp_path: pathlib.Path, template_text: str = TEMPLATE
) -> PyprojectRenderer:
    project_path = tmp_path / "subprojects" / "demo"
    project_path.mkdir(parents=True)
    (project_path / "pyproject.in.toml").write_text(template_text)

    cfg = SimpleNamespace(
        py_versions={"wrapper": "2027.2.3"},
        params=SimpleNamespace(
            wpilib_bin_version="2027.4.5",
            wpilib_bin_url="https://example.invalid/wpilib",
            mrclib_bin_version="2027.6.7",
            mrclib_bin_url="https://example.invalid/mrclib",
            mrclib_artifacts=set(),
            exclude_artifacts=set(),
            requirements={"hatch-robotpy": "~=0.2.1", "other-pkg": "~=8.1"},
            entrypoints={"robotpy_sim": "robotpy_sim.2027"},
            known_words=["CAN", "FPGA"],
        ),
        subprojects={"demo": SimpleNamespace(py_version="wrapper")},
    )
    return PyprojectRenderer(cfg, tmp_path / "subprojects")


def test_render_all_replaces_every_managed_value(tmp_path):
    rendered = make_renderer(tmp_path).render_all()["demo"]

    assert rendered.template_path.name == "pyproject.in.toml"
    assert rendered.output_path.name == "pyproject.toml"
    assert rendered.data["project"]["version"] == "2027.2.3"
    assert rendered.data["build-system"]["requires"] == ["hatch-robotpy~=0.2.1"]
    assert rendered.data["project"]["dependencies"] == [
        'other-pkg~=8.1; python_version >= "3.10"'
    ]
    assert list(rendered.data["project"]["entry-points"]) == ["robotpy_sim.2027"]
    download = rendered.data["tool"]["hatch"]["build"]["hooks"]["robotpy"][
        "maven_lib_download"
    ][0]
    assert download["repo_url"] == "https://example.invalid/wpilib"
    assert download["version"] == "2027.4.5"
    assert rendered.data["tool"]["semiwrap"]["name_transform"]["known_words"] == [
        "CAN",
        "FPGA",
    ]


def test_validate_templates_reports_non_neutral_fields(tmp_path):
    renderer = make_renderer(tmp_path)
    template = renderer.subprojects_path / "demo" / "pyproject.in.toml"
    template.write_text(TEMPLATE.replace('version = "0.0.0"', 'version = "1.2.3"', 1))

    errors = renderer.validate_templates()

    assert errors == [f"{template}: project.version must be '0.0.0', got '1.2.3'"]


def test_validate_templates_accumulates_multiple_neutral_value_errors(tmp_path):
    renderer = make_renderer(tmp_path)
    template = renderer.subprojects_path / "demo" / "pyproject.in.toml"
    template.write_text(
        TEMPLATE.replace('version = "0.0.0"', 'version = "1.2.3"', 1).replace(
            'repo_url = ""', 'repo_url = "https://example.invalid/not-neutral"'
        )
    )

    errors = renderer.validate_templates()

    assert errors == [
        f"{template}: project.version must be '0.0.0', got '1.2.3'",
        f"{template}: Maven artifact wpilibc repo_url must be '', "
        "got 'https://example.invalid/not-neutral'",
    ]


@pytest.mark.parametrize(
    ("template_text", "missing_field"),
    [
        ("[build-system]\nrequires = []\n", "project"),
        (TEMPLATE.replace('name = "demo-pkg"\n', ""), "name"),
    ],
)
def test_constructor_qualifies_missing_project_metadata(
    tmp_path, template_text, missing_field
):
    template = tmp_path / "subprojects" / "demo" / "pyproject.in.toml"

    with pytest.raises(ValueError) as exc_info:
        make_renderer(tmp_path, template_text)

    assert str(exc_info.value).startswith(f"{template}: ")
    assert missing_field in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, KeyError)


@pytest.mark.parametrize(
    ("template_text", "missing_field"),
    [
        (TEMPLATE.replace("[build-system]\n", "[unused]\n"), "build-system"),
        (
            TEMPLATE.replace(
                'dependencies = ["other-pkg==0.0.0; ' "python_version >= '3.10'\"]\n",
                "",
            ),
            "dependencies",
        ),
    ],
)
def test_validate_templates_qualifies_missing_required_fields(
    tmp_path, template_text, missing_field
):
    renderer = make_renderer(tmp_path, template_text)
    template = renderer.template_paths["demo"]

    with pytest.raises(ValueError) as exc_info:
        renderer.validate_templates()

    assert str(exc_info.value).startswith(f"{template}: ")
    assert missing_field in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, KeyError)


def test_validate_templates_qualifies_invalid_requirements(tmp_path):
    renderer = make_renderer(
        tmp_path,
        TEMPLATE.replace(
            'requires = ["hatch-robotpy==0.0.0"]',
            'requires = ["not a valid requirement !!!"]',
        ),
    )
    template = renderer.template_paths["demo"]

    with pytest.raises(ValueError) as exc_info:
        renderer.validate_templates()

    assert str(exc_info.value).startswith(f"{template}: ")
    assert isinstance(exc_info.value.__cause__, InvalidRequirement)


def test_write_creates_replaces_and_does_not_touch_identical_output(tmp_path):
    rendered = make_renderer(tmp_path).render_all()["demo"]

    assert rendered.write() is True
    assert rendered.output_path.read_text() == rendered.text

    rendered.output_path.write_text("stale")
    assert rendered.write() is True
    assert rendered.output_path.read_text() == rendered.text

    os.utime(rendered.output_path, ns=(1_000_000_000, 1_000_000_000))
    before = rendered.output_path.stat().st_mtime_ns
    assert rendered.write() is False
    assert rendered.output_path.stat().st_mtime_ns == before
