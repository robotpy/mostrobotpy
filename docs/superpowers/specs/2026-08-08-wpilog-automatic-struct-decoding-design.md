# WPILOG Automatic Struct Decoding Design

## Summary

Add an opt-in, single-pass `DataLogReader.iter_auto()` iterator that decodes primitive values and WPILib structs while preserving the existing low-level `DataLogReader` iterator unchanged. Callers may register native or user-authored `WPIStruct` types. When no matching type was supplied, a preceding `structschema` record creates and registers a dataclass with the normal RobotPy `WPIStruct` serialization contract.

Supporting schema-generated classes requires extending `wpiutil.wpistruct.make_wpistruct()` to cover the complete WPILib packed-struct grammar: characters, character arrays, enums, bitfields, fixed arrays, nesting, and all primitive storage types.

The implementation will reuse WPIUtil's native `StructDescriptorDatabase` and dynamic field layout behavior rather than introducing a second schema parser in Python.

## Motivation

A WPILOG stores struct schemas as ordinary entries:

- schema entry name: `/.schema/struct:<type-name>`
- schema entry type: `structschema`
- value entry type: `struct:<type-name>` or `struct:<type-name>[]`

The current Python `DataLogReader` exposes the schema and value payloads as bytes. Users must track entry IDs, parse schema declarations, and decode packed data themselves. RobotPy can already decode a struct when the concrete Python or native `WPIStruct` type is known, but it cannot create a type from a logged schema.

WPIUtil already contains the authoritative schema parser, descriptor database, offset calculation, enum/bitfield metadata, and dynamic field access. The missing pieces are safe Python bindings, generated `WPIStruct` dataclasses, and datalog iteration policy.

## Goals

- Preserve `DataLogReader.__iter__()` and `DataLogRecord` behavior.
- Add an ergonomic iterator that handles entry-ID bookkeeping and primitive decoding.
- Allow callers to supply predefined native or dataclass `WPIStruct` types.
- Generate a normal, reusable `WPIStruct` dataclass when a schema is encountered before its values.
- Process records in one pass and in file order.
- Support the complete WPILib packed-struct grammar.
- Keep schema layout and packing behavior aligned with allwpilib.
- Demonstrate predefined and generated struct decoding in `examples/datalog`.

## Non-goals

- Changing the result type of normal `DataLogReader` iteration.
- Grouping all samples between start and finish records.
- Sorting records by timestamp; timestamps in a datalog need not be ordered.
- Automatically decoding protobuf or MessagePack payloads.
- Exposing zero-copy native `DynamicStruct` objects whose buffers can outlive a reader record.
- Supporting forward schema references in `iter_auto()`. Normal WPILib writers emit nested schemas before schemas that reference them.

## Public API

### Automatic datalog iteration

```python
for record, entry, value in reader.iter_auto(MyStruct, Pose2d):
    print(entry.name, entry.type, record.get_timestamp(), value)
```

The method signature is conceptually:

```python
def iter_auto(
    self,
    *struct_types: type,
) -> Iterator[tuple[DataLogRecord, StartRecordData | None, object]]: ...
```

Each supplied type must satisfy the existing `WPIStruct` protocol. Types are registered by exact `wpistruct.get_type_name()` value. Supplying two different classes with the same type name raises `ValueError` before iteration.

The iterator consumes control records internally and yields one tuple for each non-control data record, in file order:

1. `record` is the existing native `DataLogRecord`.
2. `entry` is the `StartRecordData` for the currently active entry ID.
3. `value` is the automatically decoded value.

A data record whose entry ID has no active start record yields `(record, None, record.get_raw())`. Finish records remove the active entry. Set-metadata records are consumed without disrupting the active entry; `StartRecordData.metadata` continues to mean the initial metadata from the start record.

### Value decoding table

| Advertised entry type | Python value |
| --- | --- |
| `boolean` | `bool` |
| `int64` | `int` |
| `float`, `double` | `float` |
| `string`, `json` | `str` |
| primitive `[]` types | `list` |
| `raw` | `bytes` |
| unknown type | `bytes` |
| `struct:<name>` | registered `WPIStruct` instance |
| `struct:<name>[]` | `list` of registered `WPIStruct` instances |
| valid `structschema` | corresponding registered Python type |
| malformed or unrecognized `structschema` | original schema `str` |
| other schema/protobuf/MessagePack payloads | `bytes` unless already covered above |

`structschema` recognition requires both its advertised type and a schema entry name of `/.schema/struct:<name>` (also accepting the `NT:`-prefixed form used by allwpilib readers).

### Single-pass registration semantics

`iter_auto()` initializes a registry with its supplied types and then processes the log once.

When a valid struct schema record is encountered:

1. Parse it with WPIUtil's native schema parser/database.
2. If a supplied or previously generated type with that WPILib type name exists, use that type.
3. Otherwise require every nested struct referenced by the schema to already be registered.
4. Generate a dataclass, equip it with a normal `WPIStruct` descriptor, and register it.
5. Yield the Python type as the schema record's value.

When a struct value record is encountered, its type must already be registered. If it is not, raise `ValueError` with the entry name, advertised type, and timestamp. This includes values appearing before their schema and parent schemas appearing before an unregistered nested schema.

A malformed schema record yields its original text and does not register a type. A later value requiring that type therefore raises the normal unregistered-type error.

Semantically equivalent duplicate schemas, including schemas that differ only in whitespace or optional semicolons, return the already registered class. A conflicting schema for an already registered generated type raises `ValueError`; iteration must not silently reinterpret a type name. A caller-supplied type takes precedence, as the caller explicitly selected its decoder.

## Complete `make_wpistruct()` Grammar

Existing scalar, nested struct, and fixed homogeneous tuple annotations remain source compatible. New `typing.Annotated` metadata expresses schema features that ordinary Python annotations cannot represent.

```python
import dataclasses
import enum
from typing import Annotated
from wpiutil import wpistruct


class Mode(enum.IntEnum):
    OFF = 0
    AUTO = 1


@wpistruct.make_wpistruct
@dataclasses.dataclass
class Packet:
    initial: wpistruct.char
    name: Annotated[str, wpistruct.CharArray(16)]
    mode: Annotated[Mode, wpistruct.uint8]
    state: Annotated[Mode, wpistruct.uint8, wpistruct.BitField(2)]
    flags: Annotated[wpistruct.uint16, wpistruct.BitField(5)]
```

### Annotation rules

- `wpistruct.char` represents one schema `char` and behaves as a `str` whose UTF-8 representation occupies exactly one byte.
- `Annotated[str, wpistruct.CharArray(n)]` represents `char field[n]` and decodes to `str`.
- An `enum.IntEnum` annotation requires exactly one signed or unsigned sized integer metadata type, such as `wpistruct.uint8`.
- `BitField(width)` may annotate `bool`, a sized integer, or an `IntEnum` with sized integer storage.
- A boolean bitfield must have width 1.
- Existing fixed homogeneous tuples continue to represent fixed arrays. Enum arrays carry their integer storage metadata on the tuple annotation, for example `Annotated[tuple[Mode, Mode], wpistruct.uint8]`.
- Array size and bit width must be positive.
- Enum names and values come from `IntEnum.__members__`; aliases are retained in schema metadata.
- Enum definitions must fit the declared storage and bit width.
- Unsupported or duplicate metadata combinations raise `TypeError` while decorating the class.
- Existing schemas produced by existing annotations retain their current spelling and layout.

### Enum values

Unpacking a declared enum value returns the corresponding `IntEnum` member. An undeclared numeric value that fits the field creates a typed pseudo-member:

```python
assert isinstance(packet.mode, Mode)
assert packet.mode.name == "UNKNOWN_7"
assert packet.mode.value == 7
```

The pseudo-member is an instance of the annotated enum, so the runtime value agrees with the static field annotation. Creating it must not mutate the user's enum class or add it to normal enum iteration.

### Generated classes

A generated class is created with `dataclasses.make_dataclass()` and has the same observable serialization contract as a class decorated by `make_wpistruct()`:

- `dataclasses.is_dataclass(type)` is true.
- `wpistruct.get_type_name()`, `get_schema()`, `get_size()`, `pack()`, `pack_into()`, `unpack()`, and array operations work.
- The standard `WPIStruct` attribute contains `wpiutil.wpistruct.StructDescriptor`.
- Nested fields use their previously registered Python classes.
- Fixed arrays use fixed tuple annotations and tuple values.
- Enum declarations generate appropriately typed `IntEnum` classes.
- Schema spelling from the log is preserved by `wpistruct.get_schema()` even when aliases such as `float32` are used.

WPILib struct and field identifiers are preserved in schema metadata. Generated Python class names and attributes are deterministically sanitized when a schema identifier is not usable in Python (for example, a field named `class` becomes `class_`). The runtime descriptor records both the schema name and generated Python name.

All generated and user-authored `make_wpistruct()` classes expose parsed field/layout metadata through a documented `type.__wpistruct_descriptor__` attribute. The standard `WPIStruct` descriptor remains the serialization protocol consumed by existing RobotPy APIs.

## Architecture

### Native WPIUtil bridge

Bind the native schema descriptor/database functionality needed by Python. The bridge must provide:

- schema parsing and validation;
- stable struct and field metadata;
- field offsets, sizes, array sizes, enum values, nested descriptors, and bitfield layout;
- safe packing and unpacking operations for complete buffers.

Native descriptor and field wrappers retain their owning database. Database copying is disabled because native descriptors contain internal pointers. Re-registering a name must not leave Python with stale field wrappers.

Do not expose the native borrowed-buffer `DynamicStruct` constructor as the primary Python value API. A `DataLogRecord` iterator reuses native record storage, and nested native dynamic views borrow both descriptor and data lifetimes. Packing/unpacking must instead validate the complete buffer and consume or copy it synchronously.

The native database supports delayed resolution, but the higher-level `iter_auto()` registry intentionally checks validity immediately and rejects unregistered nested references.

### `wpistruct` class compiler

Refactor `wpiutil/wpistruct/dataclass.py` into separable responsibilities:

1. Resolve annotations into field declarations and Python conversion rules.
2. Compile or parse a schema into native layout metadata.
3. Build pack, pack-into, unpack, and nested-schema callbacks.
4. Attach the standard `WPIStruct` descriptor.
5. Generate a dataclass from a parsed schema when requested by the datalog iterator.

The current `struct.Struct` implementation remains the fast path for schemas containing only currently supported primitives, arrays, and nested byte blocks. Character, enum, and bitfield layouts use descriptor-backed operations. Both paths must produce identical bytes for overlapping functionality.

Pack and unpack closures retain the descriptor database and all nested Python types for their entire lifetime. A generated class therefore remains usable after the automatic iterator is exhausted or the reader is destroyed.

### `wpilog` automatic iterator

The iteration policy lives in Python where type registration, dataclass creation, and value conversion are straightforward. A small binding hook exposes `DataLogReader.iter_auto()` and delegates to the Python iterator implementation without replacing the extension type or its normal iterator.

The iterator owns:

- the supplied/generated type registry;
- the native descriptor database;
- the active entry-ID map;
- generated enum and dataclass caches.

Primitive values use existing `DataLogRecord.get_*()` methods. Registered structs use existing `wpistruct.unpack()` and `unpack_array()` functions. This avoids duplicating primitive datalog validation and keeps known native types on their established conversion path.

## Validation and Error Handling

- Existing buffer-size rules remain: a scalar struct requires exactly one struct size; an array requires a multiple of that size.
- Out-of-range integer, enum, and bitfield values raise `ValueError` while packing rather than being silently masked or truncated.
- A string that does not fit its fixed character storage raises `ValueError`; incomplete UTF-8 is never written.
- Embedded NUL bytes and valid multibyte UTF-8 follow WPIUtil's dynamic-struct behavior.
- Wrong Python field types raise `TypeError` or a wrapping `ValueError` consistent with current `make_wpistruct()` pack/unpack errors.
- Invalid annotations fail at decoration time with the class and field name in the error.
- Invalid logged schemas remain observable as strings. They do not create partially usable Python types.
- Missing type registration is an iteration error, not a raw-byte fallback, for advertised `struct:` values.
- Unknown non-struct advertised types continue to fall back to raw bytes.

## Testing

### `robotpy-wpiutil`

Preserve all current tests in `subprojects/robotpy-wpiutil/tests/test_struct.py` and add Python adaptations of the relevant cases in:

- `allwpilib/wpiutil/src/test/native/cpp/struct/DynamicStructTest.cpp`
- `allwpilib/wpiutil/src/test/native/cpp/struct/SchemaParserTest.cpp`

Coverage includes:

- empty structs;
- every primitive type and the `float32`/`float64` aliases;
- scalar and fixed-array layouts;
- nested structs;
- signed and unsigned boundary round trips;
- basic bitfields, differing storage widths, overflow to a new storage unit, and boolean bitfield placement;
- invalid bitfield types and widths;
- duplicate fields and circular references;
- character arrays containing zeroes and embedded NULs;
- valid and truncated 2-, 3-, and 4-byte UTF-8 boundaries;
- enum schema generation, aliases, known values, and unknown pseudo-members;
- exact pack/unpack parity between generated and equivalent user-authored classes;
- field-name sanitization without changing schema names;
- retention of generated classes and descriptors after the source reader/iterator is gone.

Upstream delayed-valid cases are adapted to assert the chosen higher-level behavior: `iter_auto()` rejects a parent schema if its nested type has not yet been registered, even though the lower-level native database can represent it temporarily.

### `robotpy-wpilog`

Add end-to-end reader tests for:

- each primitive and primitive array decoder;
- unknown/raw type fallback;
- caller-supplied Python and native structs;
- generated structs and struct arrays;
- schema records yielding the same class later used for values;
- nested schema registration in valid child-before-parent order;
- data before schema and parent schema before nested schema errors;
- malformed schema visibility followed by an unregistered-type error;
- equivalent and conflicting duplicate schemas;
- interleaved entry IDs, finish records, and reused IDs;
- metadata control records;
- records with no active start entry;
- preservation of ordinary `DataLogReader.__iter__()` behavior.

## Examples

Update `examples/datalog` so a user can see both workflows:

```python
# No predefined class: structschema records create dataclasses.
for record, entry, value in DataLogReader(path).iter_auto():
    print(entry.name if entry else record.get_entry(), value)
```

```python
# Prefer an existing native or make_wpistruct type.
for record, entry, value in DataLogReader(path).iter_auto(MyStruct):
    print(entry.name if entry else record.get_entry(), value)
```

The writer example will log at least one struct so the generated-type reader path can be run directly against its output.

## Compatibility

- Existing `DataLogReader` construction and iteration are unchanged.
- Existing `DataLogRecord` methods are unchanged.
- Existing `make_wpistruct()` annotations, schemas, and serialized bytes are unchanged.
- Generated classes implement the existing `WPIStruct` protocol and can be passed to existing datalog and NetworkTables APIs.
- The implementation targets the native allwpilib revision already packaged by this repository; the checked-out `../allwpilib` source and tests are the behavioral reference.
