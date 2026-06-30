import os
import subprocess
import sys
from pathlib import Path

from devtools.snake_case_migration.manifest import Ignore, Manifest, Mapping, save_manifest
from devtools.snake_case_migration.audit import (
    audit_python_source,
    audit_semiwrap_yaml_source,
)


def test_audit_reports_camel_case_defs_and_attrs():
    messages = audit_python_source(
        "def robotInit():\n    wpilib.Timer.getFPGATimestamp()\n",
        Manifest(),
    )
    assert any("robotInit" in message for message in messages)
    assert any("getFPGATimestamp" in message for message in messages)


def test_audit_labels_mapped_old_names_remaining_after_rewrite():
    manifest = Manifest(
        mappings=[
            Mapping(kind="method", old="robotInit", new="robot_init", source="test"),
        ]
    )

    messages = audit_python_source("def robotInit():\n    pass\n", manifest)

    assert messages == [
        "function: mapped old name 'robotInit' remains; expected 'robot_init'"
    ]


def test_audit_applies_scoped_mapping_to_matching_path():
    manifest = Manifest(
        mappings=[
            Mapping(
                scope="subprojects/robotpy-commands-v2/commands2/button/foo.py",
                kind="method",
                old="r_1",
                new="r1",
                source="test",
            ),
        ]
    )

    messages = audit_python_source(
        "def use():\n    r_1()\n",
        manifest,
        path="subprojects/robotpy-commands-v2/commands2/button/foo.py",
    )

    assert messages == ["name: mapped old name 'r_1' remains; expected 'r1'"]


def test_audit_skips_scoped_mapping_for_unrelated_path():
    manifest = Manifest(
        mappings=[
            Mapping(
                scope="subprojects/robotpy-commands-v2/commands2/button/foo.py",
                kind="method",
                old="r_1",
                new="r1",
                source="test",
            ),
        ]
    )

    messages = audit_python_source(
        "def use():\n    r_1()\n",
        manifest,
        path="subprojects/robotpy-wpimath/tests/geometry/test_rotation3d.py",
    )

    assert messages == []


def test_audit_applies_directory_scoped_mapping_under_directory():
    manifest = Manifest(
        mappings=[
            Mapping(
                scope="subprojects/robotpy-commands-v2/commands2/button",
                kind="method",
                old="r_1",
                new="r1",
                source="test",
            ),
        ]
    )

    messages = audit_python_source(
        "def use():\n    r_1()\n",
        manifest,
        path="subprojects/robotpy-commands-v2/commands2/button/foo.py",
    )

    assert messages == ["name: mapped old name 'r_1' remains; expected 'r1'"]


def test_audit_matches_absolute_paths_relative_to_root(tmp_path: Path):
    manifest = Manifest(
        mappings=[
            Mapping(
                scope="pkg/button",
                kind="method",
                old="r_1",
                new="r1",
                source="test",
            ),
        ]
    )
    path = tmp_path / "pkg" / "button" / "foo.py"

    messages = audit_python_source(
        "def use():\n    r_1()\n",
        manifest,
        path=path,
        root_path=tmp_path,
    )

    assert messages == ["name: mapped old name 'r_1' remains; expected 'r1'"]


def test_audit_applies_global_mapping_to_any_path():
    manifest = Manifest(
        mappings=[
            Mapping(
                scope="global",
                kind="method",
                old="r_1",
                new="r1",
                source="test",
            ),
        ]
    )

    messages = audit_python_source(
        "def use():\n    r_1()\n",
        manifest,
        path="subprojects/robotpy-wpimath/tests/geometry/test_rotation3d.py",
    )

    assert messages == ["name: mapped old name 'r_1' remains; expected 'r1'"]


def test_audit_labels_unmapped_camel_case_candidates():
    messages = audit_python_source(
        "def use():\n    possibleOldName = 1\n    MyCommand()\n    __robotInit__()\n",
        Manifest(),
    )

    assert messages == ["name: unmapped camelCase candidate 'possibleOldName'"]


def test_audit_reports_bare_function_calls_remaining_after_rewrite():
    manifest = Manifest(
        mappings=[
            Mapping(
                kind="function", old="makeCommand", new="make_command", source="test"
            ),
        ]
    )

    messages = audit_python_source(
        "def use():\n    makeCommand()\n    MyCommand()\n    __robotInit__()\n",
        manifest,
    )

    assert any("makeCommand" in message for message in messages)
    assert not any("MyCommand" in message for message in messages)
    assert not any("__robotInit__" in message for message in messages)


def test_audit_reports_parameter_definitions_remaining_after_rewrite():
    manifest = Manifest(
        mappings=[
            Mapping(
                kind="parameter", old="initialPose", new="initial_pose", source="test"
            ),
        ]
    )

    messages = audit_python_source("def reset(initialPose):\n    pass\n", manifest)

    assert any("initialPose" in message for message in messages)


def test_audit_ignores_explicit_ignored_names():
    manifest = Manifest(
        ignored=[
            Ignore(name="knownLegacyName", reason="kept for compatibility"),
        ]
    )

    messages = audit_python_source("def knownLegacyName():\n    pass\n", manifest)

    assert not messages


def test_audit_applies_scoped_ignores_only_to_matching_path():
    manifest = Manifest(
        ignored=[
            Ignore(
                scope="subprojects/robotpy-commands-v2/commands2/button/foo.py",
                name="knownLegacyName",
                reason="kept for compatibility",
            ),
        ]
    )

    matching_messages = audit_python_source(
        "def knownLegacyName():\n    pass\n",
        manifest,
        path="subprojects/robotpy-commands-v2/commands2/button/foo.py",
    )
    unrelated_messages = audit_python_source(
        "def knownLegacyName():\n    pass\n",
        manifest,
        path="subprojects/robotpy-wpimath/tests/geometry/test_rotation3d.py",
    )

    assert matching_messages == []
    assert unrelated_messages == [
        "function: unmapped camelCase candidate 'knownLegacyName'"
    ]


def test_cli_audit_scans_pyi_files(tmp_path: Path):
    manifest_path = tmp_path / "manifest.toml"
    stub_path = tmp_path / "module.pyi"
    save_manifest(
        manifest_path,
        Manifest(
            mappings=[
                Mapping(
                    kind="method",
                    old="getAngularPositionRotations",
                    new="get_angular_position_rotations",
                    source="test",
                )
            ]
        ),
    )
    stub_path.write_text("class DCMotorSim:\n    def getAngularPositionRotations(self): ...\n")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "devtools.snake_case_migration",
            "--manifest",
            str(manifest_path),
            "audit",
            str(tmp_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 1
    assert "module.pyi" in result.stdout
    assert "getAngularPositionRotations" in result.stdout


def test_cli_audit_applies_scoped_mapping_to_relative_path_from_outside_root(
    tmp_path: Path,
):
    repo_root = Path(__file__).parents[2]
    project_root = tmp_path / "project"
    manifest_path = project_root / "manifest.toml"
    source_path = project_root / "pkg" / "button" / "robot.py"
    outside_root = tmp_path / "outside"
    source_path.parent.mkdir(parents=True)
    outside_root.mkdir()
    save_manifest(
        manifest_path,
        Manifest(
            mappings=[
                Mapping(
                    scope="pkg/button",
                    kind="method",
                    old="r_1",
                    new="r1",
                    source="test",
                ),
            ]
        ),
    )
    source_path.write_text("def use():\n    r_1()\n")
    relative_source_path = Path(os.path.relpath(source_path, outside_root))
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(repo_root), env.get("PYTHONPATH", "")])
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "devtools.snake_case_migration",
            "--manifest",
            str(manifest_path),
            "audit",
            str(relative_source_path),
        ],
        cwd=outside_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 1
    assert "mapped old name 'r_1' remains; expected 'r1'" in result.stdout


def test_cli_audit_applies_manifest_relative_scope_from_subdirectory(
    tmp_path: Path,
):
    repo_root = Path(__file__).parents[2]
    project_root = tmp_path / "project"
    manifest_path = project_root / "manifest.toml"
    cwd = project_root / "pkg"
    source_path = cwd / "button" / "robot.py"
    source_path.parent.mkdir(parents=True)
    save_manifest(
        manifest_path,
        Manifest(
            mappings=[
                Mapping(
                    scope="pkg/button",
                    kind="method",
                    old="r_1",
                    new="r1",
                    source="test",
                ),
            ]
        ),
    )
    source_path.write_text("def use():\n    r_1()\n")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(repo_root), env.get("PYTHONPATH", "")])
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "devtools.snake_case_migration",
            "--manifest",
            "../manifest.toml",
            "audit",
            "button/robot.py",
        ],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 1
    assert "mapped old name 'r_1' remains; expected 'r1'" in result.stdout


def test_audit_reports_semiwrap_yaml_public_def_and_rename_names():
    messages = audit_semiwrap_yaml_source(
        '''\
classes:
  wpi::sim::DCMotorSim:
    methods:
      GetAngularPosition:
    inline_code: |
      .def("getAngularPositionRotations", [] {})
      .def_readwrite("pixelFormat", &VideoMode::pixelFormat)
      .def("robot_init", [] {})
      .def("__eq__", [] {})
      .def("lowercase", [] {})
      .def("TypeName", [] {})
      .def("_privateTypeName", [] {})
      .def("_private_value", [] {})
      .def("get_angle_degrees", [] {})
      .def("snake_case", [] {})
      .def("CxxInputIdentifier", [] {})
      .def("kValue", [] {})
      .def("OPMode", [] {})
      .def("already_snake", [] {})
      .def("getHTTPServer", [] {})
      .def_static("enumerateDevices", [] {})
    overloads:
      wpi::units::turn_t:
        rename: angularPosition
      other:
        rename: angular_position
  CxxInputIdentifier:
''',
        Manifest(
            ignored=[Ignore(name="OPMode", reason="test ignore")],
            mappings=[
                Mapping(
                    kind="method",
                    old="getHTTPServer",
                    new="get_http_server",
                    source="test",
                )
            ],
        ),
    )

    assert any(".def" in message and "getAngularPositionRotations" in message for message in messages)
    assert any(".def_readwrite" in message and "pixelFormat" in message for message in messages)
    assert any(".def_static" in message and "enumerateDevices" in message for message in messages)
    assert any("rename" in message and "angularPosition" in message for message in messages)
    assert any("getHTTPServer" in message and "expected 'get_http_server'" in message for message in messages)
    assert not any("GetAngularPosition" in message for message in messages)
    assert not any("CxxInputIdentifier" in message for message in messages)
    assert not any("'TypeName'" in message for message in messages)
    assert not any("OPMode" in message for message in messages)


def test_audit_semiwrap_yaml_applies_scoped_mapping_only_to_matching_path():
    manifest = Manifest(
        mappings=[
            Mapping(
                scope="subprojects/robotpy-wpilib/semiwrap",
                kind="method",
                old="get_r_1_button",
                new="get_r1_button",
                source="test",
            ),
        ]
    )
    source = '''\
classes:
  frc::PS4Controller:
    inline_code: |
      .def("get_r_1_button", [] {})
'''

    matching_messages = audit_semiwrap_yaml_source(
        source,
        manifest,
        path="subprojects/robotpy-wpilib/semiwrap/PS4Controller.yml",
    )
    unrelated_messages = audit_semiwrap_yaml_source(
        source,
        manifest,
        path="subprojects/robotpy-wpimath/semiwrap/Rotation3d.yml",
    )

    assert matching_messages == [
        "semiwrap .def line 4: mapped old name 'get_r_1_button' remains; expected 'get_r1_button'"
    ]
    assert unrelated_messages == []
