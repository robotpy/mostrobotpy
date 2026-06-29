from devtools.snake_case_migration.manifest import Manifest
from devtools.snake_case_migration.audit import audit_python_source


def test_audit_reports_camel_case_defs_and_attrs():
    messages = audit_python_source(
        "def robotInit():\n    wpilib.Timer.getFPGATimestamp()\n",
        Manifest(),
    )
    assert any("robotInit" in message for message in messages)
    assert any("getFPGATimestamp" in message for message in messages)
