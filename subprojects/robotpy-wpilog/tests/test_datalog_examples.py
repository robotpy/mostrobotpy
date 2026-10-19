import runpy
import subprocess
import sys
from pathlib import Path

import pytest
import wpilog

EXAMPLE_DIR = Path(__file__).parents[3] / "examples" / "datalog"


@pytest.mark.parametrize("directory", [False, True])
def test_writelog_then_printlog(tmp_path, directory):
    output = tmp_path if directory else tmp_path / "example.wpilog"

    subprocess.run(
        [sys.executable, str(EXAMPLE_DIR / "writelog.py"), str(output)],
        check=True,
        timeout=10,
    )
    if directory:
        (output,) = tmp_path.glob("*.wpilog")

    values = list(wpilog.DataLogReader(str(output)).iter_auto())
    records = [
        value
        for _, entry, value in values
        if entry is not None and entry.name == "/record"
    ]
    assert [(value.i, value.j) for value in records] == [(1, 2), (3, 4)]

    for options in ([], ["--predefined"]):
        result = subprocess.run(
            [sys.executable, str(EXAMPLE_DIR / "printlog.py"), *options, str(output)],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        lines = result.stdout.splitlines()
        for name, expected in (
            ("/bools", ["True", "False"]),
            ("/strings", ["['a', 'b', 'c']", "['d', 'e', 'f']"]),
            ("/raws", [repr(b"\x01\x02\x03"), repr(b"\x04\x05\x06")]),
            ("/record", ["ExampleRecord(i=1, j=2)", "ExampleRecord(i=3, j=4)"]),
        ):
            entries = [line for line in lines if line.startswith(f"{name} [")]
            assert len(entries) == len(expected)
            for line, value in zip(entries, expected):
                assert line.endswith(f"] {value}")


def test_writelog_flushes_when_append_fails(monkeypatch, tmp_path):
    output = tmp_path / "example.wpilog"

    class FailingEntry:
        def __init__(self, *args):
            pass

        def append(self, value):
            raise RuntimeError("intentional append failure")

    monkeypatch.setattr(wpilog, "StringArrayLogEntry", FailingEntry)
    monkeypatch.syspath_prepend(str(EXAMPLE_DIR))
    monkeypatch.setattr(sys, "argv", ["writelog.py", str(output)])

    with pytest.raises(RuntimeError, match="intentional append failure"):
        runpy.run_path(str(EXAMPLE_DIR / "writelog.py"), run_name="__main__")

    values = list(wpilog.DataLogReader(str(output)).iter_auto())
    assert [
        value
        for _, entry, value in values
        if entry is not None and entry.name == "/bools"
    ] == [True, False]
