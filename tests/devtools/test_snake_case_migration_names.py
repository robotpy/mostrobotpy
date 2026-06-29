import subprocess
import sys


def test_cli_help_runs():
    result = subprocess.run(
        [sys.executable, "-m", "devtools.snake_case_migration", "--help"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert "snake_case_migration" in result.stdout
    assert "manifest" in result.stdout
    assert "rewrite-py" in result.stdout
