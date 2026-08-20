import runpy
import subprocess
import sys
import types
from pathlib import Path

import pytest
import wpilog

EXAMPLE_DIR = Path(__file__).parents[3] / "examples" / "datalog"


def test_writelog_output_is_immediately_readable(tmp_path):
    output = tmp_path / "example.wpilog"

    subprocess.run(
        [sys.executable, str(EXAMPLE_DIR / "writelog.py"), str(output)],
        check=True,
        timeout=10,
    )

    values = list(wpilog.DataLogReader(str(output)).iter_auto())
    assert (
        sum(entry is not None and entry.name == "/record" for _, entry, _ in values)
        == 2
    )


def test_writelog_stops_background_writer_when_append_fails(monkeypatch, tmp_path):
    writers = []

    class FakeWriter:
        def __init__(self, *args):
            self.stopped = False
            writers.append(self)

        def stop(self):
            self.stopped = True

    class FailingEntry:
        def __init__(self, *args):
            pass

        def append(self, value):
            raise RuntimeError("intentional append failure")

    fake_wpilog = types.ModuleType("wpilog")
    fake_wpilog.DataLogBackgroundWriter = FakeWriter
    fake_wpilog.BooleanLogEntry = FailingEntry
    fake_wpilog.StringArrayLogEntry = FailingEntry
    fake_wpilog.RawLogEntry = FailingEntry
    fake_wpilog.StructLogEntry = FailingEntry
    monkeypatch.setitem(sys.modules, "wpilog", fake_wpilog)
    monkeypatch.syspath_prepend(str(EXAMPLE_DIR))
    monkeypatch.setattr(sys, "argv", ["writelog.py", str(tmp_path / "example.wpilog")])

    with pytest.raises(RuntimeError, match="intentional append failure"):
        runpy.run_path(str(EXAMPLE_DIR / "writelog.py"), run_name="__main__")

    assert len(writers) == 1
    assert writers[0].stopped
