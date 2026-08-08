from collections.abc import Iterator
from typing import TYPE_CHECKING

from wpiutil.wpistruct._schema import StructTypeRegistry

if TYPE_CHECKING:
    from ._wpilog import DataLogReader, DataLogRecord, StartRecordData


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


def _decode_value(record, entry, registry):
    getter = _GETTERS.get(entry.type)
    if getter is None:
        return record.get_raw()
    return getattr(record, getter)()
