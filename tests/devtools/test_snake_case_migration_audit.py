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


def test_audit_ignores_explicit_ignored_names():
    manifest = Manifest(
        ignored=[
            Ignore(name="knownLegacyName", reason="kept for compatibility"),
        ]
    )

    messages = audit_python_source("def knownLegacyName():\n    pass\n", manifest)

    assert not messages
