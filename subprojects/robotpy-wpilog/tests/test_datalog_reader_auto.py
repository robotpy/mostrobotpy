import dataclasses
from pathlib import Path

import pytest
import wpilog
from wpiutil import wpistruct


def _read_auto(path: Path, *types):
    return list(wpilog.DataLogReader(str(path)).iter_auto(*types))


@pytest.mark.parametrize(
    ("entry_cls", "value"),
    [
        (wpilog.BooleanLogEntry, True),
        (wpilog.IntegerLogEntry, -2),
        (wpilog.FloatLogEntry, 1.5),
        (wpilog.DoubleLogEntry, 2.5),
        (wpilog.StringLogEntry, "hello"),
        (wpilog.BooleanArrayLogEntry, [True, False]),
        (wpilog.IntegerArrayLogEntry, [1, -2]),
        (wpilog.FloatArrayLogEntry, [1.5, 2.5]),
        (wpilog.DoubleArrayLogEntry, [3.5, 4.5]),
        (wpilog.StringArrayLogEntry, ["a", "b"]),
    ],
)
def test_iter_auto_decodes_primitives(tmp_path, entry_cls, value):
    path = tmp_path / "primitive.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry_cls(log, "/value").append(value, 10)

    [(record, entry, decoded)] = _read_auto(path)
    assert isinstance(record, wpilog.DataLogRecord)
    assert entry.name == "/value"
    assert decoded == value


def test_iter_auto_decodes_json_as_string(tmp_path):
    path = tmp_path / "json.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry = log.start("/value", "json", "", 1)
        log.append_string(entry, '{"enabled":true}', 10)

    [(record, start, decoded)] = _read_auto(path)
    assert isinstance(record, wpilog.DataLogRecord)
    assert start.type == "json"
    assert decoded == '{"enabled":true}'


def test_iter_auto_decodes_raw_as_bytes(tmp_path):
    path = tmp_path / "raw.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry = log.start("/value", "raw", "", 1)
        log.append_raw(entry, b"\x00\x01", 10)

    [(record, start, decoded)] = _read_auto(path)
    assert isinstance(record, wpilog.DataLogRecord)
    assert start.type == "raw"
    assert decoded == b"\x00\x01"


def test_iter_auto_returns_unknown_advertised_types_as_bytes(tmp_path):
    path = tmp_path / "unknown.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry = log.start("/value", "vendor:unknown", "", 1)
        log.append_raw(entry, b"unknown", 10)

    [(record, start, decoded)] = _read_auto(path)
    assert isinstance(record, wpilog.DataLogRecord)
    assert start.type == "vendor:unknown"
    assert decoded == b"unknown"


def test_iter_auto_tracks_entry_lifecycle_and_omits_controls(tmp_path):
    path = tmp_path / "lifecycle.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry_a = log.start("/a", "int64", "initial-a", 1)
        entry_b = log.start("/b", "string", "initial-b", 2)
        log.append_integer(entry_a, 10, 3)
        log.append_string(entry_b, "first-b", 4)
        log.set_metadata(entry_a, "updated-a", 5)
        log.append_integer(entry_a, 11, 6)
        log.finish(entry_a, 7)
        log.append_raw(entry_a, b"after-finish", 8)
        reused_entry_a = log.start("/a", "double", "reused-a", 9)
        assert reused_entry_a == entry_a
        log.append_double(reused_entry_a, 2.5, 10)
        log.append_string(entry_b, "second-b", 11)
        log.append_raw(999, b"orphan", 12)

    values = _read_auto(path)

    assert [value for _, _, value in values] == [
        10,
        "first-b",
        11,
        b"after-finish",
        2.5,
        "second-b",
        b"orphan",
    ]
    assert [start.name if start else None for _, start, _ in values] == [
        "/a",
        "/b",
        "/a",
        None,
        "/a",
        "/b",
        None,
    ]
    assert [start.type if start else None for _, start, _ in values] == [
        "int64",
        "string",
        "int64",
        None,
        "double",
        "string",
        None,
    ]
    assert [start.metadata if start else None for _, start, _ in values] == [
        "initial-a",
        "initial-b",
        "initial-a",
        None,
        "reused-a",
        "initial-b",
        None,
    ]


@pytest.fixture
def log_path(tmp_path):
    path = tmp_path / "reader.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        wpilog.IntegerLogEntry(log, "/value").append(42, 10)
    return path


def test_normal_reader_iteration_is_unchanged(log_path):
    reader = wpilog.DataLogReader(str(log_path))
    values = list(reader)

    assert reader.is_valid()
    assert values
    assert all(isinstance(record, wpilog.DataLogRecord) for record in values)


def test_iter_auto_is_single_pass_and_keeps_temporary_reader_alive(log_path):
    values = wpilog.DataLogReader(str(log_path)).iter_auto()

    [(record, start, decoded)] = list(values)
    assert isinstance(record, wpilog.DataLogRecord)
    assert start.name == "/value"
    assert decoded == 42
    assert list(values) == []


@wpistruct.make_wpistruct(name="DuplicateIterAutoType")
@dataclasses.dataclass
class _FirstDuplicateType:
    value: wpistruct.uint8 = 0


@wpistruct.make_wpistruct(name="DuplicateIterAutoType")
@dataclasses.dataclass
class _SecondDuplicateType:
    value: wpistruct.uint8 = 0


def test_iter_auto_validates_supplied_types_at_method_call(log_path):
    reader = wpilog.DataLogReader(str(log_path))

    with pytest.raises(
        ValueError, match="duplicate supplied struct type DuplicateIterAutoType"
    ):
        reader.iter_auto(_FirstDuplicateType, _SecondDuplicateType)


def test_iter_auto_does_not_consume_records_at_method_call(tmp_path):
    path = tmp_path / "lazy.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry = log.start("/invalid", "int64", "", 1)
        log.append_raw(entry, b"", 2)

    values = wpilog.DataLogReader(str(path)).iter_auto()

    with pytest.raises(TypeError, match="not an integer"):
        next(values)
