import runpy
import subprocess
import sys
from pathlib import Path

import pytest
import wpilog

EXAMPLE_DIR = Path(__file__).parents[3] / "examples" / "datalog"


def _read_values(path):
    reader = wpilog.DataLogReader(str(path))
    entries = {}
    values = {}
    for record in reader:
        if record.is_start():
            start = record.get_start_data()
            entries[start.entry] = start.name
        elif record.is_finish():
            entries.pop(record.get_finish_entry(), None)
        elif not record.is_control():
            values.setdefault(entries[record.get_entry()], []).append(record.get_raw())
    return values


@pytest.mark.parametrize("directory", [False, True])
def test_writelog_emits_struct_schema_and_payloads(tmp_path, directory):
    output = tmp_path if directory else tmp_path / "example.wpilog"
    subprocess.run(
        [sys.executable, str(EXAMPLE_DIR / "writelog.py"), str(output)],
        check=True,
        timeout=10,
    )
    if directory:
        (output,) = tmp_path.glob("*.wpilog")

    values = _read_values(output)
    assert values["/.schema/struct:ExampleRecord"] == [b"int32 i; int32 j"]
    assert values["/record"] == [
        b"\x01\0\0\0\x02\0\0\0",
        b"\x03\0\0\0\x04\0\0\0",
    ]
    assert values["/bools"] == [b"\x01", b"\x00"]
    assert values["/raws"] == [b"\x01\x02\x03", b"\x04\x05\x06"]


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

    assert _read_values(output)["/bools"] == [b"\x01", b"\x00"]
