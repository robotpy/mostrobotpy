import subprocess
import sys
from pathlib import Path

import tomlkit

from devtools.snake_case_migration.manifest import (
    Ignore,
    Manifest,
    Mapping,
    load_manifest,
    merge_mapping,
    save_manifest,
)

REQUIRED_ACRONYMS = [
    "mDNS",
    "DS",
    "CAN",
    "PWM",
    "I2C",
    "SPI",
    "NT",
    "JSON",
    "PID",
    "IMU",
    "HAL",
    "JNI",
    "USB",
    "HTTP",
    "URI",
    "URL",
    "CPU",
    "FPGA",
    "FMS",
    "PCM",
    "PDP",
    "PDH",
    "RIO",
]


def test_manifest_init_cli_writes_manifest(tmp_path):
    path = tmp_path / "manifest.toml"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "devtools.snake_case_migration",
            "--manifest",
            str(path),
            "manifest",
            "init",
        ],
        check=True,
    )
    assert "[config]" in path.read_text()


def test_pyproject_cli_writes_required_name_transform_settings(tmp_path: Path):
    path = tmp_path / "pyproject.toml"
    path.write_text("[tool.semiwrap]\n")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "devtools.snake_case_migration",
            "pyproject",
            "--write",
            str(path),
        ],
        check=True,
    )

    output = path.read_text()
    assert 'name_transform.default = "snake_case"' in output
    assert 'name_transform.enum_value = "CAPS_CASE"' in output
    assert (
        tomlkit.parse(output)["tool"]["semiwrap"]["name_transform"]["acronyms"]
        == REQUIRED_ACRONYMS
    )


def test_manifest_round_trip_is_deterministic(tmp_path: Path):
    path = tmp_path / "snake_case_migration.toml"
    manifest = Manifest(
        acronyms=["DS", "FPGA"],
        mappings=[
            Mapping(
                kind="method", old="GetFPGATime", new="get_fpga_time", source="test"
            ),
            Mapping(
                kind="enum_value", old="kValueOne", new="K_VALUE_ONE", source="test"
            ),
        ],
        ignored=[Ignore(name="__iter__", reason="dunder protocol")],
    )
    save_manifest(path, manifest)
    first = path.read_text()
    loaded = load_manifest(path)
    save_manifest(path, loaded)
    assert path.read_text() == first
    assert [mapping.kind for mapping in loaded.mappings] == ["enum_value", "method"]


def test_semiwrap_bug_output_is_deterministic(tmp_path: Path):
    first_path = tmp_path / "first.toml"
    second_path = tmp_path / "second.toml"
    first = Manifest(
        acronyms=[],
        semiwrap_bugs=[
            {"name": "BetaClass", "status": "open", "reason": "second alphabetically"},
            {"name": "AlphaClass", "status": "fixed", "reason": "first alphabetically"},
        ],
    )
    second = Manifest(
        acronyms=[],
        semiwrap_bugs=[
            {"status": "fixed", "reason": "first alphabetically", "name": "AlphaClass"},
            {"status": "open", "reason": "second alphabetically", "name": "BetaClass"},
        ],
    )

    save_manifest(first_path, first)
    save_manifest(second_path, second)

    content = first_path.read_text()
    assert content == second_path.read_text()
    assert content.index('name = "AlphaClass"') < content.index('name = "BetaClass"')


def test_merge_mapping_preserves_manual_override():
    manifest = Manifest(
        mappings=[
            Mapping(
                kind="method",
                old="ConfigPythonLogging",
                new="configure_python_logging",
                source="manual",
                reason="clearer public API",
            )
        ]
    )
    merge_mapping(
        manifest,
        Mapping(
            kind="method",
            old="ConfigPythonLogging",
            new="config_python_logging",
            source="generated",
        ),
    )
    assert manifest.mappings[0].new == "configure_python_logging"
    assert manifest.mappings[0].source == "manual"
