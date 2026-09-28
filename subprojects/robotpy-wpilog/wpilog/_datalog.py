from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

from wpiutil import wpistruct
from wpiutil.wpistruct._schema import (
    InvalidStructSchema,
    StructTypeRegistry,
    _UnresolvedStructSchema,
)

if TYPE_CHECKING:
    from ._wpilog import DataLogReader, DataLogRecord, StartRecordData


_SCHEMA_PREFIX = "/.schema/struct:"
_STRUCT_PREFIX = "struct:"
_UNCACHED = object()


@dataclass
class _DataEvent:
    record: object
    entry: object
    schema_value: object = _UNCACHED
    schema_error: Exception | None = None


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
    records = iter(reader._iter_stable())
    entries = {}
    queued = deque()
    pending = {}
    pending_types = {}
    deferred_types = {}
    while True:
        try:
            event = queued.popleft() if queued else _next_data_event(records, entries)
        except StopIteration:
            return

        required = _missing_struct_type(event.entry, registry)
        if required is not None:
            _lookahead(
                required,
                event,
                records,
                entries,
                queued,
                pending,
                pending_types,
                deferred_types,
                registry,
            )
        yield event.record, event.entry, _decode_event(event, registry)


def _next_data_event(records, entries):
    while True:
        record = next(records)
        if record.is_start():
            start = record.get_start_data()
            entries[start.entry] = start
            continue
        if record.is_finish():
            entries.pop(record.get_finish_entry(), None)
            continue
        if record.is_set_metadata() or record.is_control():
            continue
        return _DataEvent(record, entries.get(record.get_entry()))


def _missing_struct_type(entry, registry):
    if entry is None:
        return None
    struct_info = _struct_type_name(entry.type)
    if struct_info is None:
        return None
    type_name, _ = struct_info
    return type_name if registry.get(type_name) is None else None


def _schema_event_type_name(event):
    if event.entry is None or event.entry.type != "structschema":
        return None
    return _schema_type_name(event.entry.name)


def _prepare_schema(event, registry):
    if event.schema_value is not _UNCACHED or event.schema_error is not None:
        return None, None

    type_name = _schema_event_type_name(event)
    try:
        schema = event.record.get_string()
        event.schema_value = registry.add_schema(type_name, schema)
    except UnicodeDecodeError as exc:
        event.schema_error = exc
    except InvalidStructSchema:
        event.schema_value = schema
    except _UnresolvedStructSchema as exc:
        return None, exc.type_name
    except ValueError as exc:
        event.schema_error = exc
    else:
        return type_name, None
    return None, None


def _prepare_ordered_schema(event, pending, pending_types, deferred_types, registry):
    type_name = _schema_event_type_name(event)
    if type_name in pending_types:
        deferred_types.setdefault(type_name, deque()).append(event)
        return None

    registered, missing = _prepare_schema(event, registry)
    if missing is not None:
        pending.setdefault(missing, []).append(event)
        pending_types[type_name] = event
    return registered


def _prepare_deferred_schemas(
    type_name, pending, pending_types, deferred_types, released, registry
):
    deferred = deferred_types.pop(type_name, ())
    while deferred:
        event = deferred.popleft()
        registered, missing = _prepare_schema(event, registry)
        if missing is not None:
            pending.setdefault(missing, []).append(event)
            pending_types[type_name] = event
            if deferred:
                deferred_types[type_name] = deferred
            return
        if registered is not None:
            released.append(registered)


def _retry_pending(registered_type, pending, pending_types, deferred_types, registry):
    released = deque((registered_type,))
    while released:
        dependency = released.popleft()
        for event in pending.pop(dependency, ()):
            registered, missing = _prepare_schema(event, registry)
            if missing is not None:
                pending.setdefault(missing, []).append(event)
                continue

            type_name = _schema_event_type_name(event)
            pending_types.pop(type_name)
            if registered is not None:
                released.append(registered)
            _prepare_deferred_schemas(
                type_name,
                pending,
                pending_types,
                deferred_types,
                released,
                registry,
            )


def _lookahead(
    required_type,
    blocked,
    records,
    entries,
    queued,
    pending,
    pending_types,
    deferred_types,
    registry,
):
    while True:
        try:
            event = _next_data_event(records, entries)
        except StopIteration:
            _decode_value(blocked.record, blocked.entry, registry)
            raise AssertionError("unreachable")

        queued.append(event)
        if _schema_event_type_name(event) is None:
            continue

        registered = _prepare_ordered_schema(
            event, pending, pending_types, deferred_types, registry
        )
        if registered is not None:
            _retry_pending(registered, pending, pending_types, deferred_types, registry)

        if registry.get(required_type) is not None:
            return


def _decode_event(event, registry):
    if event.schema_error is not None:
        raise event.schema_error
    if event.schema_value is not _UNCACHED:
        return event.schema_value
    if event.entry is None:
        return event.record.get_raw()
    return _decode_value(event.record, event.entry, registry)


def _schema_type_name(entry_name):
    _, marker, type_name = entry_name.rpartition(_SCHEMA_PREFIX)
    if not marker or not type_name:
        return None
    return type_name


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
