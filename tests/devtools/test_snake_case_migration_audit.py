from devtools.snake_case_migration.manifest import Ignore, Manifest, Mapping
from devtools.snake_case_migration.audit import audit_python_source


def test_audit_reports_camel_case_defs_and_attrs():
    messages = audit_python_source(
        "def robotInit():\n    wpilib.Timer.getFPGATimestamp()\n",
        Manifest(),
    )
    assert any("robotInit" in message for message in messages)
    assert any("getFPGATimestamp" in message for message in messages)


def test_audit_reports_mapped_old_names_remaining_after_rewrite():
    manifest = Manifest(
        mappings=[
            Mapping(kind="method", old="robotInit", new="robot_init", source="test"),
        ]
    )

    messages = audit_python_source("def robotInit():\n    pass\n", manifest)

    assert any("robotInit" in message for message in messages)


def test_audit_reports_bare_function_calls_remaining_after_rewrite():
    manifest = Manifest(
        mappings=[
            Mapping(kind="function", old="makeCommand", new="make_command", source="test"),
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
            Mapping(kind="parameter", old="initialPose", new="initial_pose", source="test"),
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
