from collections.abc import Iterator
from typing import TYPE_CHECKING

from wpiutil import wpistruct
from wpiutil.wpistruct._schema import InvalidStructSchema, StructTypeRegistry

if TYPE_CHECKING:
    from ._wpilog import DataLogReader, DataLogRecord, StartRecordData


_SCHEMA_PREFIX = "/.schema/struct:"
_STRUCT_PREFIX = "struct:"


_GETTERS = {
    "boolean": "get_boolean",
    "int64": "get_integer",
    "float": "get_float",
    "double": "get_double",
    "string": "get_string",
    "json": "get_string",
    "boolean[]": "get_boolean_array",
    "int64[]": "get_integer_array",
    "float[]": "get_float_array",
    "double[]": "get_double_array",
    "string[]": "get_string_array",
    "raw": "get_raw",
}


def _iter_auto(
    reader: "DataLogReader", struct_types: tuple[type, ...]
) -> Iterator[tuple["DataLogRecord", "StartRecordData | None", object]]:
    registry = StructTypeRegistry(struct_types)
    return _iter_records(reader, registry)


def _iter_records(reader, registry):
    entries = {}
    for record in reader:
        if record.is_start():
            start = record.get_start_data()
            entries[start.entry] = start
            continue
        if record.is_finish():
            entries.pop(record.get_finish_entry(), None)
            continue
        if record.is_set_metadata() or record.is_control():
            continue

        entry = entries.get(record.get_entry())
        if entry is None:
            yield record, None, record.get_raw()
            continue
        yield record, entry, _decode_value(record, entry, registry)


def _schema_type_name(entry_name):
    if entry_name.startswith("NT:"):
        entry_name = entry_name[3:]
    if not entry_name.startswith(_SCHEMA_PREFIX):
        return None
    name = entry_name[len(_SCHEMA_PREFIX) :]
    return name or None


def _struct_type_name(entry_type):
    if not entry_type.startswith(_STRUCT_PREFIX):
        return None
    name = entry_type[len(_STRUCT_PREFIX) :]
    is_array = name.endswith("[]")
    return (name[:-2] if is_array else name), is_array


def _decode_value(record, entry, registry):
    getter = _GETTERS.get(entry.type)
    if getter is not None:
        return getattr(record, getter)()

    if entry.type == "structschema":
        schema = record.get_string()
        type_name = _schema_type_name(entry.name)
        if type_name is None:
            return schema
        try:
            return registry.add_schema(type_name, schema)
        except InvalidStructSchema:
            return schema

    struct_info = _struct_type_name(entry.type)
    if struct_info is not None:
        type_name, is_array = struct_info
        struct_type = registry.get(type_name)
        if struct_type is None:
            raise ValueError(
                f"cannot decode entry {entry.name!r} with type {entry.type!r} "
                f"at timestamp {record.get_timestamp()}: struct type "
                f"{type_name!r} is not registered"
            )
        if is_array:
            return wpistruct.unpack_array(struct_type, record.get_raw())
        return wpistruct.unpack(struct_type, record.get_raw())

    return record.get_raw()
