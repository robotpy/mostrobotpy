import dataclasses
import gc
import weakref
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
import wpilog
from wpiutil import wpistruct


@wpistruct.make_wpistruct(name="ThingA")
@dataclasses.dataclass
class ThingA:
    value: wpistruct.uint8 = 0


@wpistruct.make_wpistruct(name="ThingArray2")
@dataclasses.dataclass
class ThingArray2:
    data: tuple[ThingA, ThingA]


@contextmanager
def _log(
    tmp_path: Path,
    filename: str,
    expected_size: int,
) -> Iterator[wpilog.DataLogWriter]:
    path = tmp_path / filename
    with wpilog.DataLogWriter(str(path)) as log:
        yield log
    assert path.stat().st_size == expected_size


def test_datalog_writer_context_manager_stops_writer(tmp_path: Path):
    path = tmp_path / "context-manager.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry = log.start("test", "int64", "", 1)
        log.append_integer(entry, 1, 2)
        assert path.stat().st_size == 0

    assert path.stat().st_size == 54


def _collect_and_churn_allocator():
    gc.collect()
    allocations = [bytearray([index % 251]) * 4096 for index in range(1024)]
    assert sum(allocation[0] for allocation in allocations) > 0
    del allocations
    gc.collect()


def test_reader_private_stable_iterator_copies_records(tmp_path: Path):
    path = tmp_path / "stable-records.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry = log.start("/value", "raw", "metadata", 1)
        log.append_raw(entry, b"first", 2)
        log.append_raw(entry, b"second", 3)

    reader = wpilog.DataLogReader(str(path))
    reader_ref = weakref.ref(reader)
    records = iter(reader._iter_stable())
    iterator_ref = weakref.ref(records)
    start_record = next(records)
    start_data = start_record.get_start_data()
    start_record_ref = weakref.ref(start_record)
    first = next(records)
    first_state = (first.get_entry(), first.get_timestamp(), first.get_raw())
    second = next(records)
    with pytest.raises(StopIteration):
        next(records)

    del reader, records, start_record
    _collect_and_churn_allocator()

    assert reader_ref() is not None
    assert iterator_ref() is not None
    assert start_record_ref() is not None
    assert start_data.entry == entry
    assert (start_data.name, start_data.type, start_data.metadata) == (
        "/value",
        "raw",
        "metadata",
    )
    assert first is not second
    assert first_state == (entry, 2, b"first")
    assert (first.get_entry(), first.get_timestamp(), first.get_raw()) == first_state
    assert (second.get_entry(), second.get_timestamp(), second.get_raw()) == (
        entry,
        3,
        b"second",
    )


def test_temporary_reader_stable_results_outlive_exhausted_iterator(tmp_path: Path):
    path = tmp_path / "temporary-stable-records.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry = log.start("/temporary", "raw", "temporary-metadata", 11)
        log.append_raw(entry, b"temporary-payload", 12)

    def read_temporary():
        reader = wpilog.DataLogReader(str(path))
        reader_ref = weakref.ref(reader)
        return list(reader._iter_stable()), reader_ref

    records, reader_ref = read_temporary()
    start_data = records[0].get_start_data()
    data_record = records[1]
    del records
    _collect_and_churn_allocator()

    assert reader_ref() is not None
    assert data_record.get_timestamp() == 12
    assert data_record.get_raw() == b"temporary-payload"
    assert start_data.entry == entry
    assert (start_data.name, start_data.type, start_data.metadata) == (
        "/temporary",
        "raw",
        "temporary-metadata",
    )


def test_metadata_record_data_keeps_source_record_alive(tmp_path: Path):
    path = tmp_path / "stable-metadata-record.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry = log.start("/value", "raw", "initial", 1)
        log.set_metadata(entry, "updated", 2)

    reader = wpilog.DataLogReader(str(path))
    reader_ref = weakref.ref(reader)
    records = iter(reader._iter_stable())
    iterator_ref = weakref.ref(records)
    next(records)
    metadata_record = next(records)
    metadata = metadata_record.get_set_metadata_data()
    metadata_record_ref = weakref.ref(metadata_record)
    del reader, records, metadata_record
    _collect_and_churn_allocator()

    assert reader_ref() is not None
    assert iterator_ref() is not None
    assert metadata_record_ref() is not None
    assert metadata.entry == entry
    assert metadata.metadata == "updated"


def test_simple_int(tmp_path: Path):
    with _log(tmp_path, "simple-int.wpilog", 54) as log:
        entry = log.start("test", "int64", "", 1)
        log.append_integer(entry, 1, 2)


@pytest.mark.parametrize(
    ("entry_cls", "value", "expected_size"),
    [
        (wpilog.BooleanLogEntry, False, 46),
        (wpilog.IntegerLogEntry, 5, 51),
        (wpilog.FloatLogEntry, 5.0, 47),
        (wpilog.DoubleLogEntry, 5.0, 52),
        (wpilog.StringLogEntry, "x", 45),
    ],
)
def test_primitive_append(tmp_path: Path, entry_cls, value, expected_size: int):
    with _log(tmp_path, f"{entry_cls.__name__}-append.wpilog", expected_size) as log:
        entry = entry_cls(log, "a", 5)
        entry.append(value, 7)


def test_boolean_update(tmp_path: Path):
    with _log(tmp_path, "boolean-first.wpilog", 46) as log:
        entry = wpilog.BooleanLogEntry(log, "a", 5)
        assert not entry.has_last_value()
        assert entry.get_last_value() is None
        entry.update(False, 7)
        assert entry.has_last_value()
        assert entry.get_last_value() is False

    with _log(tmp_path, "boolean-duplicate.wpilog", 46) as log:
        entry = wpilog.BooleanLogEntry(log, "a", 5)
        entry.update(False, 7)
        entry.update(False, 8)
        assert entry.has_last_value()
        assert entry.get_last_value() is False

    with _log(tmp_path, "boolean-changed.wpilog", 51) as log:
        entry = wpilog.BooleanLogEntry(log, "a", 5)
        entry.update(False, 7)
        entry.update(False, 8)
        entry.update(True, 9)
        assert entry.has_last_value()
        assert entry.get_last_value() is True


def test_integer_update(tmp_path: Path):
    with _log(tmp_path, "integer-first.wpilog", 51) as log:
        entry = wpilog.IntegerLogEntry(log, "a", 5)
        assert not entry.has_last_value()
        assert entry.get_last_value() is None
        entry.update(0, 7)
        assert entry.has_last_value()
        assert entry.get_last_value() == 0

    with _log(tmp_path, "integer-duplicate.wpilog", 51) as log:
        entry = wpilog.IntegerLogEntry(log, "a", 5)
        entry.update(0, 7)
        entry.update(0, 8)
        assert entry.has_last_value()
        assert entry.get_last_value() == 0

    with _log(tmp_path, "integer-changed.wpilog", 63) as log:
        entry = wpilog.IntegerLogEntry(log, "a", 5)
        entry.update(0, 7)
        entry.update(0, 8)
        entry.update(2, 9)
        assert entry.has_last_value()
        assert entry.get_last_value() == 2


def test_float_update(tmp_path: Path):
    with _log(tmp_path, "float-first.wpilog", 47) as log:
        entry = wpilog.FloatLogEntry(log, "a", 5)
        assert not entry.has_last_value()
        assert entry.get_last_value() is None
        entry.update(0.0, 7)
        assert entry.has_last_value()
        assert entry.get_last_value() == pytest.approx(0.0)

    with _log(tmp_path, "float-duplicate.wpilog", 47) as log:
        entry = wpilog.FloatLogEntry(log, "a", 5)
        entry.update(0.0, 7)
        entry.update(0.0, 8)
        assert entry.has_last_value()
        assert entry.get_last_value() == pytest.approx(0.0)

    with _log(tmp_path, "float-changed.wpilog", 55) as log:
        entry = wpilog.FloatLogEntry(log, "a", 5)
        entry.update(0.0, 7)
        entry.update(0.0, 8)
        entry.update(0.1, 9)
        assert entry.has_last_value()
        assert entry.get_last_value() == pytest.approx(0.1)


def test_double_update(tmp_path: Path):
    with _log(tmp_path, "double-first.wpilog", 52) as log:
        entry = wpilog.DoubleLogEntry(log, "a", 5)
        assert not entry.has_last_value()
        assert entry.get_last_value() is None
        entry.update(0.0, 7)
        assert entry.has_last_value()
        assert entry.get_last_value() == pytest.approx(0.0)

    with _log(tmp_path, "double-duplicate.wpilog", 52) as log:
        entry = wpilog.DoubleLogEntry(log, "a", 5)
        entry.update(0.0, 7)
        entry.update(0.0, 8)
        assert entry.has_last_value()
        assert entry.get_last_value() == pytest.approx(0.0)

    with _log(tmp_path, "double-changed.wpilog", 64) as log:
        entry = wpilog.DoubleLogEntry(log, "a", 5)
        entry.update(0.0, 7)
        entry.update(0.0, 8)
        entry.update(0.1, 9)
        assert entry.has_last_value()
        assert entry.get_last_value() == pytest.approx(0.1)


def test_string_update(tmp_path: Path):
    with _log(tmp_path, "string-first.wpilog", 45) as log:
        entry = wpilog.StringLogEntry(log, "a", 5)
        assert not entry.has_last_value()
        assert entry.get_last_value() is None
        entry.update("x", 7)
        assert entry.has_last_value()
        assert entry.get_last_value() == "x"

    with _log(tmp_path, "string-duplicate.wpilog", 45) as log:
        entry = wpilog.StringLogEntry(log, "a", 5)
        entry.update("x", 7)
        entry.update("x", 8)
        assert entry.has_last_value()
        assert entry.get_last_value() == "x"

    with _log(tmp_path, "string-y.wpilog", 50) as log:
        entry = wpilog.StringLogEntry(log, "a", 5)
        entry.update("x", 7)
        entry.update("x", 8)
        entry.update("y", 9)
        assert entry.has_last_value()
        assert entry.get_last_value() == "y"

    with _log(tmp_path, "string-yy.wpilog", 56) as log:
        entry = wpilog.StringLogEntry(log, "a", 5)
        entry.update("x", 7)
        entry.update("x", 8)
        entry.update("y", 9)
        entry.update("yy", 10)
        assert entry.has_last_value()
        assert entry.get_last_value() == "yy"

    with _log(tmp_path, "string-empty.wpilog", 60) as log:
        entry = wpilog.StringLogEntry(log, "a", 5)
        entry.update("x", 7)
        entry.update("x", 8)
        entry.update("y", 9)
        entry.update("yy", 10)
        entry.update("", 11)
        assert entry.has_last_value()
        assert entry.get_last_value() == ""


def test_raw_append(tmp_path: Path):
    with _log(tmp_path, "raw-append.wpilog", 42) as log:
        entry = wpilog.RawLogEntry(log, "a", 5)
        entry.append(bytes([5]), 7)


def test_raw_update(tmp_path: Path):
    with _log(tmp_path, "raw-first.wpilog", 42) as log:
        entry = wpilog.RawLogEntry(log, "a", 5)
        assert not entry.has_last_value()
        assert entry.get_last_value() is None
        entry.update(bytes([5]), 7)
        assert entry.has_last_value()
        assert entry.get_last_value() == [5]

    with _log(tmp_path, "raw-duplicate.wpilog", 42) as log:
        entry = wpilog.RawLogEntry(log, "a", 5)
        entry.update(bytes([5]), 7)
        entry.update(bytes([5]), 8)
        assert entry.has_last_value()
        assert entry.get_last_value() == [5]

    with _log(tmp_path, "raw-changed.wpilog", 47) as log:
        entry = wpilog.RawLogEntry(log, "a", 5)
        entry.update(bytes([5]), 7)
        entry.update(bytes([5]), 8)
        entry.update(bytes([6]), 9)
        assert entry.has_last_value()
        assert entry.get_last_value() == [6]

    with _log(tmp_path, "raw-longer.wpilog", 53) as log:
        entry = wpilog.RawLogEntry(log, "a", 5)
        entry.update(bytes([5]), 7)
        entry.update(bytes([5]), 8)
        entry.update(bytes([6]), 9)
        entry.update(bytes([6, 6]), 9)
        assert entry.has_last_value()
        assert entry.get_last_value() == [6, 6]

    with _log(tmp_path, "raw-empty.wpilog", 57) as log:
        entry = wpilog.RawLogEntry(log, "a", 5)
        entry.update(bytes([5]), 7)
        entry.update(bytes([5]), 8)
        entry.update(bytes([6]), 9)
        entry.update(bytes([6, 6]), 9)
        entry.update(b"", 10)
        assert entry.has_last_value()
        assert entry.get_last_value() == []


@pytest.mark.parametrize(
    ("entry_cls", "value", "expected_empty_size", "expected_value_size", "next_value"),
    [
        (wpilog.BooleanArrayLogEntry, [], 47, 48, [False]),
        (wpilog.IntegerArrayLogEntry, [], 45, 53, [1]),
        (wpilog.DoubleArrayLogEntry, [], 46, 54, [1.0]),
        (wpilog.FloatArrayLogEntry, [], 45, 49, [1.0]),
        (wpilog.StringArrayLogEntry, [], 50, 55, ["x"]),
    ],
)
def test_array_append_empty_and_single_value(
    tmp_path: Path,
    entry_cls,
    value: list,
    expected_empty_size: int,
    expected_value_size: int,
    next_value: list,
):
    with _log(
        tmp_path, f"{entry_cls.__name__}-empty.wpilog", expected_empty_size
    ) as log:
        entry = entry_cls(log, "a", 5)
        entry.append(value, 7)

    with _log(
        tmp_path, f"{entry_cls.__name__}-value.wpilog", expected_value_size
    ) as log:
        entry = entry_cls(log, "a", 5)
        entry.append(next_value, 7)


def test_boolean_array_update(tmp_path: Path):
    with _log(tmp_path, "boolean-array-first.wpilog", 48) as log:
        entry = wpilog.BooleanArrayLogEntry(log, "a", 5)
        assert not entry.has_last_value()
        assert entry.get_last_value() is None
        entry.update([False], 7)
        assert entry.has_last_value()
        assert entry.get_last_value() == [0]

    with _log(tmp_path, "boolean-array-duplicate.wpilog", 48) as log:
        entry = wpilog.BooleanArrayLogEntry(log, "a", 5)
        entry.update([False], 7)
        entry.update([False], 8)
        assert entry.has_last_value()
        assert entry.get_last_value() == [0]

    with _log(tmp_path, "boolean-array-changed.wpilog", 53) as log:
        entry = wpilog.BooleanArrayLogEntry(log, "a", 5)
        entry.update([False], 7)
        entry.update([False], 8)
        entry.update([True], 9)
        assert entry.has_last_value()
        assert entry.get_last_value() == [1]

    with _log(tmp_path, "boolean-array-empty.wpilog", 57) as log:
        entry = wpilog.BooleanArrayLogEntry(log, "a", 5)
        entry.update([False], 7)
        entry.update([False], 8)
        entry.update([True], 9)
        entry.update([], 10)
        assert entry.has_last_value()
        assert entry.get_last_value() == []


def test_integer_array_update(tmp_path: Path):
    with _log(tmp_path, "integer-array-first.wpilog", 53) as log:
        entry = wpilog.IntegerArrayLogEntry(log, "a", 5)
        assert not entry.has_last_value()
        assert entry.get_last_value() is None
        entry.update([1], 7)
        assert entry.has_last_value()
        assert entry.get_last_value() == [1]

    with _log(tmp_path, "integer-array-duplicate.wpilog", 53) as log:
        entry = wpilog.IntegerArrayLogEntry(log, "a", 5)
        entry.update([1], 7)
        entry.update([1], 8)
        assert entry.has_last_value()
        assert entry.get_last_value() == [1]

    with _log(tmp_path, "integer-array-changed.wpilog", 65) as log:
        entry = wpilog.IntegerArrayLogEntry(log, "a", 5)
        entry.update([1], 7)
        entry.update([1], 8)
        entry.update([2], 9)
        assert entry.has_last_value()
        assert entry.get_last_value() == [2]

    with _log(tmp_path, "integer-array-empty.wpilog", 69) as log:
        entry = wpilog.IntegerArrayLogEntry(log, "a", 5)
        entry.update([1], 7)
        entry.update([1], 8)
        entry.update([2], 9)
        entry.update([], 10)
        assert entry.has_last_value()
        assert entry.get_last_value() == []


def test_double_array_update(tmp_path: Path):
    with _log(tmp_path, "double-array-first.wpilog", 54) as log:
        entry = wpilog.DoubleArrayLogEntry(log, "a", 5)
        assert not entry.has_last_value()
        assert entry.get_last_value() is None
        entry.update([1.0], 7)
        assert entry.has_last_value()
        assert entry.get_last_value() == [1.0]

    with _log(tmp_path, "double-array-duplicate.wpilog", 54) as log:
        entry = wpilog.DoubleArrayLogEntry(log, "a", 5)
        entry.update([1.0], 7)
        entry.update([1.0], 8)
        assert entry.has_last_value()
        assert entry.get_last_value() == [1.0]

    with _log(tmp_path, "double-array-changed.wpilog", 66) as log:
        entry = wpilog.DoubleArrayLogEntry(log, "a", 5)
        entry.update([1.0], 7)
        entry.update([1.0], 8)
        entry.update([2.0], 9)
        assert entry.has_last_value()
        assert entry.get_last_value() == [2.0]

    with _log(tmp_path, "double-array-empty.wpilog", 70) as log:
        entry = wpilog.DoubleArrayLogEntry(log, "a", 5)
        entry.update([1.0], 7)
        entry.update([1.0], 8)
        entry.update([2.0], 9)
        entry.update([], 10)
        assert entry.has_last_value()
        assert entry.get_last_value() == []


def test_float_array_update(tmp_path: Path):
    with _log(tmp_path, "float-array-first.wpilog", 49) as log:
        entry = wpilog.FloatArrayLogEntry(log, "a", 5)
        assert not entry.has_last_value()
        assert entry.get_last_value() is None
        entry.update([1.0], 7)
        assert entry.has_last_value()
        assert entry.get_last_value() == pytest.approx([1.0])

    with _log(tmp_path, "float-array-duplicate.wpilog", 49) as log:
        entry = wpilog.FloatArrayLogEntry(log, "a", 5)
        entry.update([1.0], 7)
        entry.update([1.0], 8)
        assert entry.has_last_value()
        assert entry.get_last_value() == pytest.approx([1.0])

    with _log(tmp_path, "float-array-changed.wpilog", 57) as log:
        entry = wpilog.FloatArrayLogEntry(log, "a", 5)
        entry.update([1.0], 7)
        entry.update([1.0], 8)
        entry.update([2.0], 9)
        assert entry.has_last_value()
        assert entry.get_last_value() == pytest.approx([2.0])

    with _log(tmp_path, "float-array-empty.wpilog", 61) as log:
        entry = wpilog.FloatArrayLogEntry(log, "a", 5)
        entry.update([1.0], 7)
        entry.update([1.0], 8)
        entry.update([2.0], 9)
        entry.update([], 10)
        assert entry.has_last_value()
        assert entry.get_last_value() == []


def test_string_array_update(tmp_path: Path):
    with _log(tmp_path, "string-array-first.wpilog", 55) as log:
        entry = wpilog.StringArrayLogEntry(log, "a", 5)
        assert not entry.has_last_value()
        assert entry.get_last_value() is None
        entry.update(["x"], 7)
        assert entry.has_last_value()
        assert entry.get_last_value() == ["x"]

    with _log(tmp_path, "string-array-duplicate.wpilog", 55) as log:
        entry = wpilog.StringArrayLogEntry(log, "a", 5)
        entry.update(["x"], 7)
        entry.update(["x"], 8)
        assert entry.has_last_value()
        assert entry.get_last_value() == ["x"]

    with _log(tmp_path, "string-array-changed.wpilog", 68) as log:
        entry = wpilog.StringArrayLogEntry(log, "a", 5)
        entry.update(["x"], 7)
        entry.update(["x"], 8)
        entry.update(["y"], 9)
        assert entry.has_last_value()
        assert entry.get_last_value() == ["y"]

    with _log(tmp_path, "string-array-empty.wpilog", 76) as log:
        entry = wpilog.StringArrayLogEntry(log, "a", 5)
        entry.update(["x"], 7)
        entry.update(["x"], 8)
        entry.update(["y"], 9)
        entry.update([], 10)
        assert entry.has_last_value()
        assert entry.get_last_value() == []


def test_struct_a_append(tmp_path: Path):
    path = tmp_path / "struct-a-append.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry = wpilog.StructLogEntry(log, "a", ThingA, 5)
        entry.append(ThingA())
        entry.append(ThingA(), 7)
    assert path.stat().st_size > 0


def test_struct_update(tmp_path: Path):
    with _log(tmp_path, "struct-first.wpilog", 122) as log:
        entry = wpilog.StructLogEntry(log, "a", ThingA, 5)
        assert not entry.has_last_value()
        assert entry.get_last_value() is None
        entry.update(ThingA(), 7)
        assert entry.has_last_value()
        assert entry.get_last_value() == ThingA()

    with _log(tmp_path, "struct-duplicate.wpilog", 122) as log:
        entry = wpilog.StructLogEntry(log, "a", ThingA, 5)
        entry.update(ThingA(), 7)
        entry.update(ThingA(), 8)
        assert entry.has_last_value()
        assert entry.get_last_value() == ThingA()

    with _log(tmp_path, "struct-changed.wpilog", 127) as log:
        entry = wpilog.StructLogEntry(log, "a", ThingA, 5)
        entry.update(ThingA(), 7)
        entry.update(ThingA(), 8)
        entry.update(ThingA(1), 9)
        assert entry.has_last_value()
        assert entry.get_last_value() == ThingA(1)


def test_struct_array_a_append(tmp_path: Path):
    path = tmp_path / "struct-array-a-append.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry = wpilog.StructArrayLogEntry(log, "a", ThingA, 5)
        entry.append([ThingA(), ThingA()])
        entry.append([ThingA(), ThingA()], 7)
    assert path.stat().st_size > 0


def test_struct_array_update(tmp_path: Path):
    with _log(tmp_path, "struct-array-first.wpilog", 125) as log:
        entry = wpilog.StructArrayLogEntry(log, "a", ThingA, 5)
        assert not entry.has_last_value()
        assert entry.get_last_value() is None
        entry.update([ThingA(), ThingA(1)], 7)
        assert entry.has_last_value()
        assert entry.get_last_value() == [ThingA(), ThingA(1)]

    with _log(tmp_path, "struct-array-duplicate.wpilog", 125) as log:
        entry = wpilog.StructArrayLogEntry(log, "a", ThingA, 5)
        entry.update([ThingA(), ThingA(1)], 7)
        entry.update([ThingA(), ThingA(1)], 8)
        assert entry.has_last_value()
        assert entry.get_last_value() == [ThingA(), ThingA(1)]

    with _log(tmp_path, "struct-array-changed.wpilog", 131) as log:
        entry = wpilog.StructArrayLogEntry(log, "a", ThingA, 5)
        entry.update([ThingA(), ThingA(1)], 7)
        entry.update([ThingA(), ThingA(1)], 8)
        entry.update([ThingA(), ThingA(2)], 9)
        assert entry.has_last_value()
        assert entry.get_last_value() == [ThingA(), ThingA(2)]

    with _log(tmp_path, "struct-array-empty.wpilog", 135) as log:
        entry = wpilog.StructArrayLogEntry(log, "a", ThingA, 5)
        entry.update([ThingA(), ThingA(1)], 7)
        entry.update([ThingA(), ThingA(1)], 8)
        entry.update([ThingA(), ThingA(2)], 9)
        entry.update([], 10)
        assert entry.has_last_value()
        assert entry.get_last_value() == []


def test_struct_fixed_array_equivalent(tmp_path: Path):
    path = tmp_path / "struct-fixed-array-equivalent.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry = wpilog.StructLogEntry(log, "a", ThingArray2, 5)
        value = ThingArray2((ThingA(), ThingA()))
        entry.append(value)
        entry.append(value, 7)
    assert path.stat().st_size > 0
