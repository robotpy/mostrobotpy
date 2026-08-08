import dataclasses
from pathlib import Path

import pytest
import wpilog
from wpiutil import wpistruct


@wpistruct.make_wpistruct(name="Reading")
@dataclasses.dataclass
class Reading:
    i: wpistruct.int32 = 0
    j: wpistruct.int32 = 0


@wpistruct.make_wpistruct(name="ReadingChild")
@dataclasses.dataclass
class ReadingChild:
    value: wpistruct.uint8 = 0


@wpistruct.make_wpistruct(name="ReadingParent")
@dataclasses.dataclass
class ReadingParent:
    child: ReadingChild = dataclasses.field(default_factory=ReadingChild)


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


def test_iter_auto_decodes_registered_struct(tmp_path):
    path = tmp_path / "registered-struct.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        wpilog.StructLogEntry(log, "/reading", Reading).append(Reading(1, 2), 10)

    values = _read_auto(path, Reading)
    schemas = [value for _, entry, value in values if entry.type == "structschema"]
    readings = [value for _, entry, value in values if entry.type == "struct:Reading"]

    assert schemas == [Reading]
    assert readings == [Reading(1, 2)]


def test_iter_auto_decodes_generated_struct(tmp_path):
    path = tmp_path / "generated-struct.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        wpilog.StructLogEntry(log, "/reading", Reading).append(Reading(3, 4), 10)

    values = _read_auto(path)
    [generated] = [value for _, entry, value in values if entry.type == "structschema"]
    [instance] = [value for _, entry, value in values if entry.type == "struct:Reading"]

    assert isinstance(generated, type)
    assert dataclasses.is_dataclass(generated)
    assert type(instance) is generated
    assert dataclasses.asdict(instance) == {"i": 3, "j": 4}


def test_iter_auto_decodes_registered_struct_array(tmp_path):
    path = tmp_path / "registered-struct-array.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        wpilog.StructArrayLogEntry(log, "/readings", Reading).append(
            [Reading(1, 2), Reading(3, 4)], 10
        )

    values = _read_auto(path, Reading)
    [readings] = [
        value for _, entry, value in values if entry.type == "struct:Reading[]"
    ]

    assert readings == [Reading(1, 2), Reading(3, 4)]


def test_iter_auto_decodes_generated_struct_array(tmp_path):
    path = tmp_path / "generated-struct-array.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        wpilog.StructArrayLogEntry(log, "/readings", Reading).append(
            [Reading(5, 6), Reading(7, 8)], 10
        )

    values = _read_auto(path)
    [generated] = [value for _, entry, value in values if entry.type == "structschema"]
    [readings] = [
        value for _, entry, value in values if entry.type == "struct:Reading[]"
    ]

    assert all(type(reading) is generated for reading in readings)
    assert [dataclasses.asdict(reading) for reading in readings] == [
        {"i": 5, "j": 6},
        {"i": 7, "j": 8},
    ]


def test_iter_auto_generated_type_is_reusable(tmp_path):
    source = tmp_path / "source.wpilog"
    with wpilog.DataLogWriter(str(source)) as log:
        wpilog.StructLogEntry(log, "/reading", Reading).append(Reading(1, 2), 10)

    source_values = _read_auto(source)
    generated = next(
        value for _, entry, value in source_values if entry.type == "structschema"
    )
    instance = next(
        value for _, entry, value in source_values if entry.type == "struct:Reading"
    )

    destination = tmp_path / "destination.wpilog"
    with wpilog.DataLogWriter(str(destination)) as log:
        wpilog.StructLogEntry(log, "/copy", generated).append(instance, 20)

    copied = [
        value
        for _, entry, value in _read_auto(destination, generated)
        if entry.type == "struct:Reading"
    ]
    assert copied == [instance]


def test_iter_auto_generates_nested_structs_child_first(tmp_path):
    path = tmp_path / "nested-struct.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        wpilog.StructLogEntry(log, "/parent", ReadingParent).append(
            ReadingParent(ReadingChild(9)), 10
        )

    values = _read_auto(path)
    schema_values = [
        (entry.name, value)
        for _, entry, value in values
        if entry.type == "structschema"
    ]
    [parent] = [
        value for _, entry, value in values if entry.type == "struct:ReadingParent"
    ]

    assert [name for name, _ in schema_values] == [
        "/.schema/struct:ReadingChild",
        "/.schema/struct:ReadingParent",
    ]
    generated_child = schema_values[0][1]
    generated_parent = schema_values[1][1]
    assert type(parent) is generated_parent
    assert type(parent.child) is generated_child
    assert parent.child.value == 9


def test_iter_auto_missing_struct_registration_has_record_context(tmp_path):
    path = tmp_path / "late-schema.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry = log.start("/value", "struct:Late", "", 1)
        log.append_raw(entry, b"\x01", 2)
        log.add_schema("struct:Late", "structschema", "uint8 value", 3)

    with pytest.raises(ValueError) as exc_info:
        _read_auto(path)

    message = str(exc_info.value)
    assert "/value" in message
    assert "struct:Late" in message
    assert "2" in message


def test_iter_auto_parent_schema_before_child_raises(tmp_path):
    path = tmp_path / "parent-before-child.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        parent = log.start("/.schema/struct:Parent", "structschema", "", 1)
        log.append_string(parent, "Child child", 2)
        child = log.start("/.schema/struct:Child", "structschema", "", 3)
        log.append_string(child, "uint8 value", 4)

    with pytest.raises(ValueError, match="Child"):
        _read_auto(path)


def test_iter_auto_malformed_schema_yields_text_then_value_raises(tmp_path):
    path = tmp_path / "malformed-schema.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        schema = log.start("/.schema/struct:Bad", "structschema", "", 1)
        log.append_string(schema, "uint8 [2]", 2)
        value = log.start("/value", "struct:Bad", "", 3)
        log.append_raw(value, b"\x01\x02", 4)

    values = wpilog.DataLogReader(str(path)).iter_auto()
    schema_record, schema_entry, schema_value = next(values)
    assert schema_record.get_timestamp() == 2
    assert schema_entry.type == "structschema"
    assert schema_value == "uint8 [2]"

    with pytest.raises(ValueError, match=r"/value.*struct:Bad.*4"):
        next(values)


def test_iter_auto_equivalent_duplicate_schemas_reuse_generated_type(tmp_path):
    path = tmp_path / "duplicate-equivalent.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        first = log.start("/.schema/struct:Duplicate", "structschema", "", 1)
        log.append_string(first, "uint8 value", 2)
        log.finish(first, 3)
        second = log.start("/.schema/struct:Duplicate", "structschema", "", 4)
        log.append_string(second, "  uint8 value;  ", 5)

    schema_types = [value for _, _, value in _read_auto(path)]
    assert len(schema_types) == 2
    assert schema_types[0] is schema_types[1]


def test_iter_auto_conflicting_duplicate_schemas_raise(tmp_path):
    path = tmp_path / "duplicate-conflicting.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        first = log.start("/.schema/struct:Duplicate", "structschema", "", 1)
        log.append_string(first, "uint8 value", 2)
        log.finish(first, 3)
        second = log.start("/.schema/struct:Duplicate", "structschema", "", 4)
        log.append_string(second, "uint16 value", 5)

    values = wpilog.DataLogReader(str(path)).iter_auto()
    first_record = next(values)
    assert isinstance(first_record[2], type)
    with pytest.raises(ValueError, match="Duplicate"):
        next(values)


def test_iter_auto_supplied_type_precedes_incompatible_logged_schema(tmp_path):
    path = tmp_path / "supplied-precedence.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        schema = log.start("/.schema/struct:Reading", "structschema", "", 1)
        log.append_string(schema, "uint8 incompatible", 2)
        value = log.start("/reading", "struct:Reading", "", 3)
        log.append_raw(value, wpistruct.pack(Reading(11, 12)), 4)

    values = _read_auto(path, Reading)
    assert [value for _, entry, value in values if entry.type == "structschema"] == [
        Reading
    ]
    assert [value for _, entry, value in values if entry.type == "struct:Reading"] == [
        Reading(11, 12)
    ]


def test_iter_auto_recognizes_nt_schema_name(tmp_path):
    path = tmp_path / "nt-schema.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        schema = log.start("NT:/.schema/struct:Reading", "structschema", "", 1)
        log.append_string(schema, "int32 i; int32 j", 2)
        value = log.start("/reading", "struct:Reading", "", 3)
        log.append_raw(value, wpistruct.pack(Reading(13, 14)), 4)

    values = _read_auto(path)
    [generated] = [value for _, entry, value in values if entry.type == "structschema"]
    [reading] = [value for _, entry, value in values if entry.type == "struct:Reading"]
    assert type(reading) is generated
    assert dataclasses.asdict(reading) == {"i": 13, "j": 14}


def test_iter_auto_ignores_unrecognized_structschema_entry_name(tmp_path):
    path = tmp_path / "unrecognized-schema.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        schema = log.start("/.schema/protobuf:Reading", "structschema", "", 1)
        log.append_string(schema, "int32 i; int32 j", 2)
        value = log.start("/reading", "struct:Reading", "", 3)
        log.append_raw(value, wpistruct.pack(Reading(15, 16)), 4)

    values = wpilog.DataLogReader(str(path)).iter_auto()
    _, schema_entry, schema_value = next(values)
    assert schema_entry.name == "/.schema/protobuf:Reading"
    assert schema_value == "int32 i; int32 j"
    with pytest.raises(ValueError, match=r"/reading.*struct:Reading.*4"):
        next(values)


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


@wpistruct.make_wpistruct(name="Reading")
@dataclasses.dataclass
class _OtherReading:
    value: wpistruct.uint8 = 0


def test_iter_auto_validates_supplied_types_at_method_call(log_path):
    reader = wpilog.DataLogReader(str(log_path))

    with pytest.raises(ValueError, match="duplicate supplied struct type Reading"):
        reader.iter_auto(Reading, _OtherReading)


def test_iter_auto_does_not_consume_records_at_method_call(tmp_path):
    path = tmp_path / "lazy.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        entry = log.start("/invalid", "int64", "", 1)
        log.append_raw(entry, b"", 2)

    values = wpilog.DataLogReader(str(path)).iter_auto()

    with pytest.raises(TypeError, match="not an integer"):
        next(values)
