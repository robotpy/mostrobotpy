from pathlib import Path

from devtools.snake_case_migration.manifest import (
    Ignore,
    Manifest,
    Mapping,
    load_manifest,
    merge_mapping,
    save_manifest,
)


def test_manifest_round_trip_is_deterministic(tmp_path: Path):
    path = tmp_path / "snake_case_migration.toml"
    manifest = Manifest(
        acronyms=["DS", "FPGA"],
        mappings=[
            Mapping(kind="method", old="GetFPGATime", new="get_fpga_time", source="test"),
            Mapping(kind="enum_value", old="kValueOne", new="K_VALUE_ONE", source="test"),
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
        Mapping(kind="method", old="ConfigPythonLogging", new="config_python_logging", source="generated"),
    )
    assert manifest.mappings[0].new == "configure_python_logging"
    assert manifest.mappings[0].source == "manual"
