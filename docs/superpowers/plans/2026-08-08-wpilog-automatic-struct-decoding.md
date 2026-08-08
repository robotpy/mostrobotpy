# WPILOG Automatic Struct Decoding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add single-pass `DataLogReader.iter_auto()` decoding for primitives and registered/generated WPILib structs, and extend `make_wpistruct()` to support the complete packed-struct grammar.

**Architecture:** Add a lifetime-safe native schema/layout bridge that exposes immutable descriptor snapshots plus synchronous whole-buffer codecs, then refactor Python `wpistruct` around a shared field-plan compiler used by authored and schema-generated dataclasses. Implement `iter_auto()` as Python policy reached through a small pybind method so ordinary native reader iteration remains unchanged.

**Tech Stack:** Python 3.11+, C++23, pybind11, semiwrap, Meson, WPIUtil `StructDescriptorDatabase`/`DynamicStruct`, dataclasses, `typing.Annotated`, pytest, Black.

## Global Constraints

- Preserve `DataLogReader.__iter__()`, `DataLogRecord`, and all existing reader methods unchanged.
- `iter_auto()` is single-pass, yields data records in file order, and does not support forward struct-schema references.
- Yield `(DataLogRecord, StartRecordData | None, object)` for each non-control data record.
- Supplied `WPIStruct` types take precedence and are keyed by exact `wpistruct.get_type_name()`.
- Missing registration for an advertised `struct:` value raises `ValueError`; unknown non-struct types return raw `bytes`.
- Valid `structschema` values yield Python types; malformed schemas yield their original strings without registration.
- Generated classes are normal mutable dataclasses with the standard `WPIStruct` serialization descriptor.
- Support the complete WPILib packed-struct grammar, including chars, char arrays, enums, bitfields, arrays, nesting, and primitive aliases.
- Existing `make_wpistruct()` annotations, schemas, serialized bytes, and pack/unpack error wrappers remain compatible.
- Do not expose borrowed native `DynamicStruct` objects to Python.
- Native descriptor wrappers must retain database ownership and must not permit stale field pointers after redefinition.
- Packing rejects out-of-range numbers and oversized strings instead of silently masking or truncating.
- Use `../allwpilib/wpiutil/src/test/native/cpp/struct/DynamicStructTest.cpp` and `SchemaParserTest.cpp` as behavioral references.
- Build through `./rdev.sh`; run each subproject's `tests/run_tests.py`; format Python with Black.

---

## File Structure

### Native schema bridge

- Create `subprojects/robotpy-wpiutil/wpiutil/src/wpistruct/wpystruct_schema.h`: lifetime-safe schema database/descriptor wrapper declarations and whole-buffer codec declarations.
- Create `subprojects/robotpy-wpiutil/wpiutil/src/wpistruct/wpystruct_schema.cpp`: native schema parsing, immutable field snapshots, semantic duplicate checks, and synchronous pack/unpack.
- Create `subprojects/robotpy-wpiutil/semiwrap/WPyStructSchema.yml`: expose the internal bridge in `_wpiutil._schema` while keeping borrowed native dynamic classes hidden and out of public `wpistruct` imports.
- Modify `subprojects/robotpy-wpiutil/pyproject.toml`: register the bridge header.
- Modify `subprojects/robotpy-wpiutil/meson.build`: compile the bridge source.

### Python struct compiler

- Modify `subprojects/robotpy-wpiutil/wpiutil/wpistruct/dataclass.py`: retain public decorator and scalar marker types; add `char`, `CharArray`, and `BitField`; delegate compilation.
- Create `subprojects/robotpy-wpiutil/wpiutil/wpistruct/layout.py`: public immutable `StructLayout` and `StructFieldLayout` metadata.
- Create `subprojects/robotpy-wpiutil/wpiutil/wpistruct/_compiler.py`: annotation field plans, legacy fast codec, descriptor codec, enum conversion, and `WPIStruct` attachment.
- Create `subprojects/robotpy-wpiutil/wpiutil/wpistruct/_schema.py`: schema-to-dataclass generation, identifier sanitization, schema registry, and duplicate/conflict policy.
- Modify `subprojects/robotpy-wpiutil/wpiutil/wpistruct/__init__.py`: export new marker and layout APIs.
- Modify `subprojects/robotpy-wpiutil/wpiutil/wpistruct/desc.py`: document the relationship between `WPIStruct` and `__wpistruct_descriptor__`; do not change the existing tuple fields.

### Automatic datalog iterator

- Create `subprojects/robotpy-wpilog/wpilog/_datalog.py`: entry tracking, primitive dispatch, schema recognition, type registry integration, and tuple generation.
- Modify `subprojects/robotpy-wpilog/semiwrap/DataLogReader.yml`: add `iter_auto(*struct_types)` that lazily delegates to `_datalog._iter_auto()`.

### Tests and examples

- Create `subprojects/robotpy-wpiutil/tests/test_schema_bridge.py`: native bridge metadata, ownership, and codec tests.
- Create `subprojects/robotpy-wpiutil/tests/test_struct_annotations.py`: complete authored-dataclass grammar tests.
- Create `subprojects/robotpy-wpiutil/tests/test_struct_schema.py`: schema-generated class and registry tests.
- Preserve and extend `subprojects/robotpy-wpiutil/tests/test_struct.py`: legacy compatibility and zero-size regression tests.
- Create `subprojects/robotpy-wpilog/tests/test_datalog_reader_auto.py`: end-to-end automatic iterator tests for Python-authored and generated types.
- Create `subprojects/robotpy-wpimath/tests/geometry/test_datalog_struct.py`: mandatory CI integration test for a native-capsule `Pose2d` type.
- Create `examples/datalog/datalog_struct.py`: shared example dataclass.
- Modify `examples/datalog/writelog.py`: write a struct entry.
- Modify `examples/datalog/printlog.py`: demonstrate generated and predefined decoding.

---

### Task 1: Add lifetime-safe schema descriptor bindings

**Files:**
- Create: `subprojects/robotpy-wpiutil/wpiutil/src/wpistruct/wpystruct_schema.h`
- Create: `subprojects/robotpy-wpiutil/wpiutil/src/wpistruct/wpystruct_schema.cpp`
- Create: `subprojects/robotpy-wpiutil/semiwrap/WPyStructSchema.yml`
- Modify: `subprojects/robotpy-wpiutil/pyproject.toml`
- Modify: `subprojects/robotpy-wpiutil/meson.build`
- Test: `subprojects/robotpy-wpiutil/tests/test_schema_bridge.py`

**Interfaces:**
- Produces internal `_wpiutil._schema.SchemaDatabase` with `add(name, schema) -> SchemaDescriptor` and `find(name) -> SchemaDescriptor | None`.
- Produces internal immutable `SchemaDescriptor` properties: `name`, `schema`, `is_valid`, `size`, and `fields`.
- Produces internal immutable `SchemaFieldDescriptor` properties: `name`, `type`, `size`, `offset`, `array_size`, `bit_width`, `bit_shift`, `bit_mask`, `enum_values`, and `struct_name`.
- Later tasks consume these exact names from `wpiutil._wpiutil._schema`.

- [ ] **Step 1: Write failing descriptor metadata and validation tests**

Create `subprojects/robotpy-wpiutil/tests/test_schema_bridge.py` with:

```python
import gc

import pytest

from wpiutil._wpiutil._schema import SchemaDatabase


def test_schema_descriptor_metadata():
    db = SchemaDatabase()
    desc = db.add("Packet", "int32 count; uint16 flags:3")

    assert desc.name == "Packet"
    assert desc.schema == "int32 count; uint16 flags:3"
    assert desc.is_valid
    assert desc.size == 6
    assert [field.name for field in desc.fields] == ["count", "flags"]
    assert desc.fields[0].type == "int32"
    assert desc.fields[0].offset == 0
    assert desc.fields[1].offset == 4
    assert desc.fields[1].bit_width == 3
    assert desc.fields[1].bit_shift == 0
    assert desc.fields[1].bit_mask == 0x7


def test_schema_descriptor_nested_delayed_validity():
    db = SchemaDatabase()
    outer = db.add("Outer", "Inner value")
    assert not outer.is_valid
    with pytest.raises(ValueError, match="descriptor Outer is not valid"):
        _ = outer.size

    db.add("Inner", "int32 value")
    assert outer.is_valid
    assert outer.size == 4
    assert outer.fields[0].struct_name == "Inner"


def test_schema_descriptor_parse_error():
    db = SchemaDatabase()
    with pytest.raises(ValueError, match="expected identifier"):
        db.add("Bad", "int32 [2]")


def test_schema_descriptor_retains_database():
    desc = SchemaDatabase().add("Value", "uint8 value")
    gc.collect()
    assert desc.size == 1
    assert desc.fields[0].name == "value"
```

- [ ] **Step 2: Run the descriptor test to verify the binding is absent**

Run:

```bash
python -m pytest subprojects/robotpy-wpiutil/tests/test_schema_bridge.py -vv
```

Expected: collection fails because `SchemaDatabase` is not exported.

- [ ] **Step 3: Declare owner-sharing wrapper types**

In `wpystruct_schema.h`, declare wrappers with shared implementation ownership rather than exposing native pointers:

```cpp
namespace wpy::structs {

class SchemaDatabaseImpl;

struct SchemaFieldDescriptor {
  std::string name;
  std::string type;
  size_t size;
  size_t offset;
  size_t arraySize;
  unsigned int bitWidth;
  unsigned int bitShift;
  uint64_t bitMask;
  std::vector<std::pair<std::string, int64_t>> enumValues;
  std::optional<std::string> structName;
};

class SchemaDescriptor {
 public:
  std::string GetName() const;
  std::string GetSchema() const;
  bool IsValid() const;
  size_t GetSize() const;
  std::vector<SchemaFieldDescriptor> GetFields() const;

 private:
  friend class SchemaDatabase;
  SchemaDescriptor(std::shared_ptr<SchemaDatabaseImpl> impl, std::string name);
  std::shared_ptr<SchemaDatabaseImpl> m_impl;
  std::string m_name;
};

class SchemaDatabase {
 public:
  SchemaDatabase();
  SchemaDescriptor Add(std::string_view name, std::string_view schema);
  std::optional<SchemaDescriptor> Find(std::string_view name) const;

 private:
  std::shared_ptr<SchemaDatabaseImpl> m_impl;
};

}  // namespace wpy::structs
```

`SchemaDatabaseImpl` owns the native `wpi::util::StructDescriptorDatabase` plus a map of explicitly registered schema strings. `SchemaDescriptor` resolves the native descriptor by name on every property access; field objects are value snapshots, so no Python object retains a pointer into `StructDescriptor::m_fields`.

- [ ] **Step 4: Implement descriptor parsing and guarded access**

In `wpystruct_schema.cpp`:

- Call native `Add(name, schema, &err)` and raise `py::value_error(err)` when it returns null.
- Permit filling a native unresolved placeholder only when the name has no explicit schema in the wrapper's definition map.
- For an already defined name, parse/compare declarations without mutating the live database; return the existing descriptor for semantic equality and raise `ValueError("conflicting schema for <name>")` otherwise.
- In `GetSize()`, check `IsValid()` before calling native `GetSize()` so C++ assertions are unreachable from Python.
- Convert native field types to their schema spellings (`bool`, `char`, `int8`, ..., `float`, `double`, or nested struct name).

- [ ] **Step 5: Register the header and source with semiwrap/Meson**

Add to `subprojects/robotpy-wpiutil/pyproject.toml` under `[tool.semiwrap.extension_modules."wpiutil._wpiutil".headers]`:

```toml
WPyStructSchema = "src/wpistruct/wpystruct_schema.h"
```

Add to `wpiutil_sources` in `subprojects/robotpy-wpiutil/meson.build`:

```meson
'wpiutil/src/wpistruct/wpystruct_schema.cpp',
```

Create `semiwrap/WPyStructSchema.yml` with this structure (list every `SchemaFieldDescriptor` attribute shown in the Task 1 interface as read-only):

```yaml
defaults:
  subpackage: _schema

classes:
  wpy::structs::SchemaFieldDescriptor:
    attributes:
      name:
        access: readonly
      type:
        access: readonly
      size:
        access: readonly
      offset:
        access: readonly
      arraySize:
        access: readonly
      bitWidth:
        access: readonly
      bitShift:
        access: readonly
      bitMask:
        access: readonly
      enumValues:
        access: readonly
      structName:
        access: readonly
  wpy::structs::SchemaDescriptor:
    methods:
      SchemaDescriptor:
        ignore: true
      GetName:
        no_release_gil: true
      GetSchema:
        no_release_gil: true
      IsValid:
        no_release_gil: true
      GetSize:
        no_release_gil: true
      GetFields:
        no_release_gil: true
  wpy::structs::SchemaDatabase:
    methods:
      Add:
        no_release_gil: true
      Find:
        no_release_gil: true

inline_code: |
  cls_SchemaDescriptor
    .def_property_readonly("name", &wpy::structs::SchemaDescriptor::GetName)
    .def_property_readonly("schema", &wpy::structs::SchemaDescriptor::GetSchema)
    .def_property_readonly("is_valid", &wpy::structs::SchemaDescriptor::IsValid)
    .def_property_readonly("size", &wpy::structs::SchemaDescriptor::GetSize)
    .def_property_readonly("fields", &wpy::structs::SchemaDescriptor::GetFields);
```

Keep `SchemaDatabase` default-constructible. Because `_schema` is not listed in `tool.semiwrap.update_init`, these implementation types do not leak into public `wpiutil` or `wpistruct` imports.

- [ ] **Step 6: Build the editable wpiutil package**

Run:

```bash
./rdev.sh develop robotpy-wpiutil
```

Expected: semiwrap and Meson complete without generated-binding or linker errors.

- [ ] **Step 7: Run descriptor tests and existing struct tests**

Run:

```bash
python -m pytest subprojects/robotpy-wpiutil/tests/test_schema_bridge.py subprojects/robotpy-wpiutil/tests/test_struct.py -vv
```

Expected: both files pass.

- [ ] **Step 8: Commit the descriptor bridge**

```bash
git add subprojects/robotpy-wpiutil/pyproject.toml \
  subprojects/robotpy-wpiutil/meson.build \
  subprojects/robotpy-wpiutil/semiwrap/WPyStructSchema.yml \
  subprojects/robotpy-wpiutil/wpiutil/src/wpistruct/wpystruct_schema.h \
  subprojects/robotpy-wpiutil/wpiutil/src/wpistruct/wpystruct_schema.cpp \
  subprojects/robotpy-wpiutil/tests/test_schema_bridge.py
git commit -m "feat(wpiutil): bind packed struct schemas"
```

---

### Task 2: Add safe whole-buffer schema codecs

**Files:**
- Modify: `subprojects/robotpy-wpiutil/wpiutil/src/wpistruct/wpystruct_schema.h`
- Modify: `subprojects/robotpy-wpiutil/wpiutil/src/wpistruct/wpystruct_schema.cpp`
- Modify: `subprojects/robotpy-wpiutil/semiwrap/WPyStructSchema.yml`
- Modify: `subprojects/robotpy-wpiutil/tests/test_schema_bridge.py`

**Interfaces:**
- Consumes: Task 1 `SchemaDescriptor`.
- Produces: `_wpiutil._schema.pack_schema(descriptor, values) -> bytes`.
- Produces: `_wpiutil._schema.unpack_schema(descriptor, buffer) -> tuple`.
- Nested struct fields consume/produce exact-size `bytes`; Python conversion to nested classes belongs to Task 4.
- Fixed non-char arrays consume Python sequences and unpack to tuples; char arrays consume/produce `str`.

- [ ] **Step 1: Write failing primitive, array, and nested codec tests**

Append to `test_schema_bridge.py`:

```python
from wpiutil._wpiutil._schema import pack_schema, unpack_schema


@pytest.mark.parametrize(
    ("schema", "value", "encoded"),
    [
        ("bool value", True, b"\x01"),
        ("int8 value", -2, b"\xfe"),
        ("uint16 value", 0x1234, b"\x34\x12"),
        ("int32 value", -3, b"\xfd\xff\xff\xff"),
        ("float value", 1.5, b"\x00\x00\xc0?"),
        ("double value", 1.5, b"\x00\x00\x00\x00\x00\x00\xf8?"),
    ],
)
def test_schema_primitive_round_trip(schema, value, encoded):
    desc = SchemaDatabase().add("Value", schema)
    assert pack_schema(desc, (value,)) == encoded
    assert unpack_schema(desc, encoded) == (value,)


def test_schema_array_and_nested_round_trip():
    db = SchemaDatabase()
    db.add("Inner", "int16 value")
    outer = db.add("Outer", "uint8 samples[2]; Inner inner")
    encoded = pack_schema(outer, ((1, 2), b"\xfe\xff"))
    assert encoded == b"\x01\x02\xfe\xff"
    assert unpack_schema(outer, encoded) == ((1, 2), b"\xfe\xff")
```

- [ ] **Step 2: Write failing bitfield, enum, and UTF-8 tests adapted from allwpilib**

Append tests asserting:

```python
def test_schema_bitfield_layout_and_sign_extension():
    desc = SchemaDatabase().add("Bits", "int16 signed:3; bool ready:1; uint16 count:4")
    encoded = pack_schema(desc, (-1, True, 9))
    assert encoded == b"\x9f\x00"
    assert unpack_schema(desc, encoded) == (-1, True, 9)


def test_schema_enum_is_an_integer_at_native_boundary():
    desc = SchemaDatabase().add("Mode", "enum {OFF=0,AUTO=1} uint8 mode")
    assert pack_schema(desc, (1,)) == b"\x01"
    assert unpack_schema(desc, b"\x07") == (7,)
    assert desc.fields[0].enum_values == [("OFF", 0), ("AUTO", 1)]


def test_schema_char_array_preserves_embedded_nul():
    desc = SchemaDatabase().add("Text", "char text[5]")
    assert pack_schema(desc, ("ab\0c",)) == b"ab\0c\0"
    assert unpack_schema(desc, b"ab\0c\0") == ("ab\0c",)


def test_schema_char_array_rejects_utf8_truncation():
    desc = SchemaDatabase().add("Text", "char text[2]")
    with pytest.raises(ValueError, match="text.*2 bytes"):
        pack_schema(desc, ("a\u1234",))
```

- [ ] **Step 3: Run the new tests to verify codec functions are absent**

```bash
python -m pytest subprojects/robotpy-wpiutil/tests/test_schema_bridge.py -vv
```

Expected: import fails for `pack_schema` and `unpack_schema`.

- [ ] **Step 4: Declare synchronous codec functions**

Add to `wpystruct_schema.h`:

```cpp
py::bytes PackSchema(const SchemaDescriptor& desc, const py::sequence& values);
py::tuple UnpackSchema(const SchemaDescriptor& desc, const py::buffer& buffer);
```

Expose them in `WPyStructSchema.yml` as:

```yaml
functions:
  PackSchema:
    no_release_gil: true
  UnpackSchema:
    no_release_gil: true
```

The default snake-case transform produces `pack_schema` and `unpack_schema` in the internal `_schema` subpackage.

- [ ] **Step 5: Implement guarded recursive field conversion**

In `wpystruct_schema.cpp`:

- Resolve the native descriptor from the wrapper immediately before each operation.
- Require descriptor validity and `len(values) == len(fields)`.
- Allocate a temporary zero-filled vector of exactly `descriptor.GetSize()` for packing.
- Validate Python types, fixed-array lengths, integer/bitfield ranges, enum storage ranges, and nested byte lengths before calling native setters.
- Treat `char` and `char[]` as strings; call `SetStringField()` and raise if it reports truncation.
- Correct signed bitfield unpacking by sign-extending from `field.GetBitWidth()`, not the containing storage size.
- Return nested fields as owned `bytes` and arrays of nested fields as tuples of owned `bytes`.
- Validate one-dimensional byte buffers and exact size before constructing stack-local `DynamicStruct`.
- Copy the temporary vector into Python `bytes` only after all fields succeed, making packing atomic.

- [ ] **Step 6: Add explicit validation regression tests**

Add tests for:

```python
def test_schema_codec_validation():
    desc = SchemaDatabase().add("Value", "uint8 value; int8 nibble:4")

    with pytest.raises(ValueError, match="expected 2 fields"):
        pack_schema(desc, (1,))
    with pytest.raises(ValueError, match="value.*0.*255"):
        pack_schema(desc, (256, 0))
    with pytest.raises(ValueError, match="nibble.*-8.*7"):
        pack_schema(desc, (1, 8))
    with pytest.raises(ValueError, match="buffer must be 2 bytes"):
        unpack_schema(desc, b"\x00")
```

Add the exact upstream scalar limits and representative bitfield layouts:

```python
@pytest.mark.parametrize(
    ("schema", "minimum", "maximum"),
    [
        ("int8 value", -(2**7), 2**7 - 1),
        ("int16 value", -(2**15), 2**15 - 1),
        ("int32 value", -(2**31), 2**31 - 1),
        ("int64 value", -(2**63), 2**63 - 1),
        ("uint8 value", 0, 2**8 - 1),
        ("uint16 value", 0, 2**16 - 1),
        ("uint32 value", 0, 2**32 - 1),
        ("uint64 value", 0, 2**64 - 1),
    ],
)
def test_schema_integer_limits(schema, minimum, maximum):
    desc = SchemaDatabase().add("Value", schema)
    for value in (minimum, maximum):
        assert unpack_schema(desc, pack_schema(desc, (value,))) == (value,)


@pytest.mark.parametrize(
    ("schema", "values", "size"),
    [
        ("int32 a:2; uint32 b:30", (-1, 100), 4),
        ("int32 a:2; int16 b:2", (-1, -2), 6),
        ("int8 a:4; int8 b:5", (-1, -2), 2),
        ("int16 a:2; bool b:1; bool c:1; uint16 d:5", (-1, True, False, 17), 2),
    ],
)
def test_schema_bitfield_placement(schema, values, size):
    desc = SchemaDatabase().add("Bits", schema)
    assert desc.size == size
    assert unpack_schema(desc, pack_schema(desc, values)) == values
```

- [ ] **Step 7: Build and run bridge tests**

```bash
./rdev.sh develop robotpy-wpiutil
python -m pytest subprojects/robotpy-wpiutil/tests/test_schema_bridge.py -vv
```

Expected: all bridge tests pass.

- [ ] **Step 8: Commit the schema codecs**

```bash
git add subprojects/robotpy-wpiutil/wpiutil/src/wpistruct/wpystruct_schema.h \
  subprojects/robotpy-wpiutil/wpiutil/src/wpistruct/wpystruct_schema.cpp \
  subprojects/robotpy-wpiutil/semiwrap/WPyStructSchema.yml \
  subprojects/robotpy-wpiutil/tests/test_schema_bridge.py
git commit -m "feat(wpiutil): add safe dynamic struct codecs"
```

---

### Task 3: Refactor `make_wpistruct` around field plans and add metadata markers

**Files:**
- Create: `subprojects/robotpy-wpiutil/wpiutil/wpistruct/layout.py`
- Create: `subprojects/robotpy-wpiutil/wpiutil/wpistruct/_compiler.py`
- Modify: `subprojects/robotpy-wpiutil/wpiutil/wpistruct/dataclass.py`
- Modify: `subprojects/robotpy-wpiutil/wpiutil/wpistruct/__init__.py`
- Modify: `subprojects/robotpy-wpiutil/wpiutil/wpistruct/desc.py`
- Modify: `subprojects/robotpy-wpiutil/tests/test_struct.py`
- Create: `subprojects/robotpy-wpiutil/tests/test_struct_annotations.py`

**Interfaces:**
- Produces public `wpistruct.char`, `wpistruct.CharArray(size)`, `wpistruct.BitField(width)`, `StructLayout`, and `StructFieldLayout`.
- Produces internal `_compiler.compile_wpistruct(cls, struct_name, *, schema_override=None, descriptor=None, python_names=None) -> type`.
- Every decorated class gains `__wpistruct_descriptor__: StructLayout` while retaining the existing `WPIStruct: StructDescriptor`.
- Task 5 consumes `compile_wpistruct()` for generated dataclasses.

- [ ] **Step 1: Add marker validation and legacy-compatibility tests**

Create `test_struct_annotations.py` with:

```python
import dataclasses
from typing import Annotated

import pytest

from wpiutil import wpistruct


def test_char_marker():
    assert wpistruct.char("x") == "x"
    assert wpistruct.char("\0") == "\0"
    with pytest.raises(ValueError, match="exactly one UTF-8 byte"):
        wpistruct.char("\u1234")


def test_metadata_marker_validation():
    assert wpistruct.CharArray(4).size == 4
    assert wpistruct.BitField(3).width == 3
    with pytest.raises(ValueError, match="positive"):
        wpistruct.CharArray(0)
    with pytest.raises(ValueError, match="positive"):
        wpistruct.BitField(-1)


@wpistruct.make_wpistruct(name="Legacy")
@dataclasses.dataclass
class Legacy:
    count: int
    values: tuple[wpistruct.uint16, wpistruct.uint16]


def test_legacy_schema_and_bytes_remain_exact():
    assert wpistruct.get_schema(Legacy) == "int32 count; uint16 values[2]"
    assert wpistruct.pack(Legacy(1, (2, 3))) == b"\x01\0\0\0\x02\0\x03\0"
    assert wpistruct.unpack(Legacy, b"\x01\0\0\0\x02\0\x03\0") == Legacy(1, (2, 3))
```

Extend `test_struct.py` with an empty dataclass scalar round trip and assert `wpistruct.unpack_array(Empty, b"")` raises `ValueError` instead of dividing by zero.

- [ ] **Step 2: Run marker tests to verify they fail**

```bash
python -m pytest subprojects/robotpy-wpiutil/tests/test_struct_annotations.py subprojects/robotpy-wpiutil/tests/test_struct.py -vv
```

Expected: new exports are absent and the zero-size array regression fails.

- [ ] **Step 3: Implement marker and layout value types**

In `dataclass.py`, add:

```python
class char(str):
    def __new__(cls, value: str, /):
        if not isinstance(value, str):
            raise TypeError("char value must be str")
        if len(value.encode("utf-8")) != 1:
            raise ValueError("char value must occupy exactly one UTF-8 byte")
        return super().__new__(cls, value)


@dataclasses.dataclass(frozen=True, slots=True)
class CharArray:
    size: int

    def __post_init__(self):
        if isinstance(self.size, bool) or not isinstance(self.size, int) or self.size <= 0:
            raise ValueError("CharArray size must be a positive integer")


@dataclasses.dataclass(frozen=True, slots=True)
class BitField:
    width: int

    def __post_init__(self):
        if isinstance(self.width, bool) or not isinstance(self.width, int) or self.width <= 0:
            raise ValueError("BitField width must be a positive integer")
```

In `layout.py`, add frozen/slotted `StructFieldLayout` and `StructLayout` with the exact public fields approved in the spec:

```python
@dataclasses.dataclass(frozen=True, slots=True)
class StructFieldLayout:
    schema_name: str
    python_name: str
    type_name: str
    offset: int
    size: int
    array_size: int
    bit_width: int
    bit_shift: int
    bit_mask: int
    enum_values: tuple[tuple[str, int], ...]
    nested_type: type | None


@dataclasses.dataclass(frozen=True, slots=True)
class StructLayout:
    type_name: str
    schema: str
    size: int
    fields: tuple[StructFieldLayout, ...]
```

- [ ] **Step 4: Extract current compiler behavior into field plans**

In `_compiler.py`, define a private `FieldPlan` dataclass and move annotation resolution, schema construction, fast `struct.Struct` format construction, nested pack/unpack conversion, and `WPIStruct` attachment out of `dataclass.py`. Use:

```python
resolved_hints = typing.get_type_hints(cls, include_extras=True)
```

Preserve current schema spelling, `for_each_nested()` ordering, generated pack/unpack error messages, tuple collision behavior, and fast-path bytes. `dataclass.make_wpistruct()` remains the public decorator and delegates to `compile_wpistruct()`.

Build a native schema descriptor for every class solely to populate `__wpistruct_descriptor__`; existing simple values continue through the current `struct.Struct` codec.

- [ ] **Step 5: Guard zero-size array unpacking**

In `wpystruct_fns.cpp::unpackArray()`, check `sz == 0` before modulo/division and raise:

```cpp
if (sz == 0) {
  throw py::value_error("cannot unpack an array of zero-size structs");
}
```

Scalar empty structs remain supported.

- [ ] **Step 6: Export the new public types and document metadata**

Update `wpistruct/__init__.py` to export `char`, `CharArray`, `BitField`, `StructLayout`, and `StructFieldLayout`. Update `desc.py` documentation to state that `WPIStruct` remains the serializer descriptor and `__wpistruct_descriptor__` is parsed field/layout metadata; do not alter `StructDescriptor` tuple shape.

- [ ] **Step 7: Format, build, and run legacy plus marker tests**

```bash
black subprojects/robotpy-wpiutil/wpiutil/wpistruct \
  subprojects/robotpy-wpiutil/tests/test_struct.py \
  subprojects/robotpy-wpiutil/tests/test_struct_annotations.py
./rdev.sh develop robotpy-wpiutil
python -m pytest subprojects/robotpy-wpiutil/tests/test_struct.py \
  subprojects/robotpy-wpiutil/tests/test_struct_annotations.py -vv
```

Expected: all old tests and new marker tests pass.

- [ ] **Step 8: Commit the compiler refactor**

```bash
git add subprojects/robotpy-wpiutil/wpiutil/wpistruct \
  subprojects/robotpy-wpiutil/wpiutil/src/wpistruct/wpystruct_fns.cpp \
  subprojects/robotpy-wpiutil/tests/test_struct.py \
  subprojects/robotpy-wpiutil/tests/test_struct_annotations.py
git commit -m "refactor(wpiutil): compile wpistruct field plans"
```

---

### Task 4: Support chars, enums, and bitfields in authored dataclasses

**Files:**
- Modify: `subprojects/robotpy-wpiutil/wpiutil/wpistruct/_compiler.py`
- Modify: `subprojects/robotpy-wpiutil/tests/test_struct_annotations.py`

**Interfaces:**
- Consumes: Task 2 `pack_schema()`/`unpack_schema()` and Task 3 markers/layout.
- Produces complete `make_wpistruct()` support for `char`, `Annotated[str, CharArray(n)]`, `Annotated[IntEnum, sized_int]`, and `BitField(width)`.
- Produces internal `_enum_from_int(enum_type, value, cache) -> IntEnum` that does not mutate the enum class.

- [ ] **Step 1: Write failing authored char and enum tests**

Append to `test_struct_annotations.py`:

```python
import enum


class Mode(enum.IntEnum):
    OFF = 0
    AUTO = 1
    DEFAULT = 1


@wpistruct.make_wpistruct(name="Packet")
@dataclasses.dataclass
class Packet:
    initial: wpistruct.char
    name: Annotated[str, wpistruct.CharArray(5)]
    mode: Annotated[Mode, wpistruct.uint8]


def test_char_and_enum_schema_round_trip():
    value = Packet(wpistruct.char("A"), "ab\0c", Mode.AUTO)
    assert wpistruct.get_schema(Packet) == (
        "char initial; char name[5]; "
        "enum {OFF=0,AUTO=1,DEFAULT=1} uint8 mode"
    )
    assert wpistruct.unpack(Packet, wpistruct.pack(value)) == value


def test_unknown_enum_value_is_typed_without_mutating_enum():
    before = dict(Mode.__members__)
    value = wpistruct.unpack(Packet, b"Aab\0c\0\x07")
    assert isinstance(value.mode, Mode)
    assert value.mode.name == "UNKNOWN_7"
    assert value.mode.value == 7
    assert Mode.__members__ == before
    assert list(Mode) == [Mode.OFF, Mode.AUTO]
```

- [ ] **Step 2: Write failing bitfield layout and validation tests**

Define authored dataclasses for these upstream layouts and assert exact schema, size, and bytes:

```python
@wpistruct.make_wpistruct
@dataclasses.dataclass
class SharedBits:
    a: Annotated[wpistruct.int16, wpistruct.BitField(2)]
    b: Annotated[bool, wpistruct.BitField(1)]
    c: Annotated[bool, wpistruct.BitField(1)]
    d: Annotated[wpistruct.uint16, wpistruct.BitField(5)]


def test_shared_bitfield_round_trip():
    value = SharedBits(-1, True, False, 17)
    assert wpistruct.get_size(SharedBits) == 2
    assert wpistruct.pack(value) == b"\x17\x01"
    assert wpistruct.unpack(SharedBits, b"\x17\x01") == value
```

Define and parameterize these authored classes so the Python compiler exercises every upstream storage transition:

```python
@wpistruct.make_wpistruct
@dataclasses.dataclass
class DifferentWidthBits:
    a: Annotated[wpistruct.int32, wpistruct.BitField(2)]
    b: Annotated[wpistruct.int16, wpistruct.BitField(2)]


@wpistruct.make_wpistruct
@dataclasses.dataclass
class OverflowBits:
    a: Annotated[wpistruct.int8, wpistruct.BitField(4)]
    b: Annotated[wpistruct.int8, wpistruct.BitField(5)]


@wpistruct.make_wpistruct
@dataclasses.dataclass
class BoolFirst8:
    a: Annotated[bool, wpistruct.BitField(1)]
    b: Annotated[wpistruct.int8, wpistruct.BitField(5)]


@wpistruct.make_wpistruct
@dataclasses.dataclass
class BoolFirst16:
    a: Annotated[bool, wpistruct.BitField(1)]
    b: Annotated[wpistruct.int16, wpistruct.BitField(5)]


@wpistruct.make_wpistruct
@dataclasses.dataclass
class BoolAfterFullUnit:
    a: Annotated[wpistruct.int16, wpistruct.BitField(16)]
    b: Annotated[bool, wpistruct.BitField(1)]


@pytest.mark.parametrize(
    ("struct_type", "value", "size"),
    [
        (DifferentWidthBits, DifferentWidthBits(-1, -2), 6),
        (OverflowBits, OverflowBits(-1, -2), 2),
        (BoolFirst8, BoolFirst8(True, -2), 1),
        (BoolFirst16, BoolFirst16(True, -2), 3),
        (BoolAfterFullUnit, BoolAfterFullUnit(-1, True), 3),
    ],
)
def test_authored_bitfield_storage_transitions(struct_type, value, size):
    assert wpistruct.get_size(struct_type) == size
    assert wpistruct.unpack(struct_type, wpistruct.pack(value)) == value
```

Add exact decoration-time validation tests:

```python
class Huge(enum.IntEnum):
    VALUE = 256


@pytest.mark.parametrize(
    ("annotation", "match"),
    [
        (Annotated[float, wpistruct.BitField(1)], "cannot be bitfield"),
        (Annotated[wpistruct.char, wpistruct.BitField(1)], "cannot be bitfield"),
        (Annotated[Legacy, wpistruct.BitField(1)], "cannot be bitfield"),
        (Annotated[bool, wpistruct.BitField(2)], "width must be 1"),
        (Annotated[wpistruct.int16, wpistruct.BitField(17)], "exceeds type size"),
        (Mode, "requires sized integer storage"),
        (Annotated[Mode, wpistruct.uint8, wpistruct.int16], "multiple storage"),
        (
            Annotated[tuple[wpistruct.int8, wpistruct.int8], wpistruct.BitField(2)],
            "array.*bitfield",
        ),
        (Annotated[Huge, wpistruct.uint8], "VALUE.*does not fit"),
    ],
)
def test_invalid_complete_grammar_annotations(annotation, match):
    cls = dataclasses.make_dataclass("InvalidField", [("value", annotation)])
    with pytest.raises(TypeError, match=match):
        wpistruct.make_wpistruct(cls)
```

- [ ] **Step 3: Run focused tests and verify the new annotations fail**

```bash
python -m pytest subprojects/robotpy-wpiutil/tests/test_struct_annotations.py -vv
```

Expected: annotation resolution rejects or ignores the new metadata.

- [ ] **Step 4: Parse and validate complete `Annotated` metadata**

Extend `FieldPlan` resolution to separate the base annotation from metadata, accept metadata in any order, and enforce:

- exactly one `CharArray` only on `str`;
- exactly one sized integer marker on `IntEnum` or tuple-of-`IntEnum`;
- at most one `BitField`;
- bitfields only on bool, sized integers, or sized enums;
- no array bitfields;
- storage and bit-width ranges for every enum member.

Generate enum declarations from `IntEnum.__members__.items()` so aliases remain present.

- [ ] **Step 5: Add descriptor-backed pack/unpack conversion**

For any class containing char, enum, or bitfield fields:

- Convert dataclass values to the ordered primitive/tuple/bytes sequence accepted by `pack_schema()`.
- Require enum instances when packing enum fields.
- Convert nested objects to bytes with existing `wpistruct.pack()`.
- Call `unpack_schema()`, then convert known enum integers through `_enum_from_int()` and nested bytes through existing `wpistruct.unpack()`.
- Wrap errors with the same `<typename>: error packing data` / `error unpacking data` messages used by the existing compiler.
- Make `pack_into()` build complete bytes first, then replace the destination buffer only after success.

Implement pseudo-members with `int.__new__(enum_type, value)`, `_name_ = f"UNKNOWN_{value}"`, and `_value_ = value`, cached per field plan without modifying `_member_map_`, `_value2member_map_`, or `__members__`.

- [ ] **Step 6: Add UTF-8 and numeric boundary tests**

Port the upstream 2-, 3-, and 4-byte UTF-8 fit/truncation boundaries as authored `CharArray` tests. Assert overlong strings raise `ValueError` and leave an existing `pack_into()` destination unchanged. Add minimum/maximum signed, unsigned, and signed-bitfield round trips plus one-beyond-range failures.

- [ ] **Step 7: Format and run all wpiutil struct tests**

```bash
black subprojects/robotpy-wpiutil/wpiutil/wpistruct/_compiler.py \
  subprojects/robotpy-wpiutil/tests/test_struct_annotations.py
./rdev.sh develop robotpy-wpiutil
python -m pytest subprojects/robotpy-wpiutil/tests/test_struct.py \
  subprojects/robotpy-wpiutil/tests/test_schema_bridge.py \
  subprojects/robotpy-wpiutil/tests/test_struct_annotations.py -vv
```

Expected: all tests pass.

- [ ] **Step 8: Commit complete authored grammar support**

```bash
git add subprojects/robotpy-wpiutil/wpiutil/wpistruct/_compiler.py \
  subprojects/robotpy-wpiutil/tests/test_struct_annotations.py
git commit -m "feat(wpiutil): support complete wpistruct annotations"
```

---

### Task 5: Generate `WPIStruct` dataclasses from schemas

**Files:**
- Create: `subprojects/robotpy-wpiutil/wpiutil/wpistruct/_schema.py`
- Create: `subprojects/robotpy-wpiutil/tests/test_struct_schema.py`
- Modify: `subprojects/robotpy-wpiutil/wpiutil/wpistruct/_compiler.py`
- Modify: `subprojects/robotpy-wpiutil/wpiutil/wpistruct/dataclass.py`

**Interfaces:**
- Produces internal `InvalidStructSchema(ValueError)`.
- Produces internal `make_wpistruct_from_schema(name, schema, *, nested, descriptor=None) -> type`.
- Produces internal `StructTypeRegistry(struct_types)` with `get(type_name) -> type | None` and `add_schema(type_name, schema) -> type`.
- Task 7 imports `StructTypeRegistry` and catches only `InvalidStructSchema` for malformed schema text.

- [ ] **Step 1: Write failing generated primitive, enum, and parity tests**

Create `test_struct_schema.py`:

```python
import dataclasses
import enum

import pytest

from wpiutil import wpistruct
from wpiutil.wpistruct._schema import (
    InvalidStructSchema,
    StructTypeRegistry,
    make_wpistruct_from_schema,
)


def test_generate_struct_from_schema():
    generated = make_wpistruct_from_schema(
        "Packet",
        "int32 count; char name[4]; enum {OFF=0,AUTO=1} uint8 mode",
        nested={},
    )
    assert dataclasses.is_dataclass(generated)
    assert wpistruct.get_type_name(generated) == "Packet"
    assert wpistruct.get_schema(generated) == (
        "int32 count; char name[4]; enum {OFF=0,AUTO=1} uint8 mode"
    )
    mode_type = generated.__dataclass_fields__["mode"].type
    value = wpistruct.unpack(generated, b"\x02\0\0\0abc\0\x01")
    assert value.count == 2
    assert value.name == "abc"
    assert isinstance(value.mode, mode_type)
    assert value.mode.name == "AUTO"
    assert wpistruct.pack(value) == b"\x02\0\0\0abc\0\x01"
```

- [ ] **Step 2: Write failing nesting, sanitization, alias, and lifetime tests**

Add these nesting, sanitization, alias, array, empty-schema, and lifetime tests:

```python
import gc


def test_generated_nested_struct_and_sanitized_field():
    inner = make_wpistruct_from_schema("Inner", "float32 value", nested={})
    outer = make_wpistruct_from_schema(
        "pkg::Outer", "Inner class; float64 total", nested={"Inner": inner}
    )
    value = wpistruct.unpack(outer, b"\0\0\xc0?\0\0\0\0\0\0\x04@")
    assert value.class_.value == 1.5
    assert value.total == 2.5
    assert wpistruct.get_schema(outer) == "Inner class; float64 total"
    schemas = []
    wpistruct.for_each_nested(outer, lambda type_name, schema: schemas.append((type_name, schema)))
    assert schemas == [
        ("struct:Inner", "float32 value"),
        ("struct:pkg::Outer", "Inner class; float64 total"),
    ]
    assert outer.__wpistruct_descriptor__.type_name == "pkg::Outer"
    assert outer.__wpistruct_descriptor__.fields[0].schema_name == "class"
    assert outer.__wpistruct_descriptor__.fields[0].python_name == "class_"


def test_generated_fixed_arrays():
    inner = make_wpistruct_from_schema("Inner", "uint8 value", nested={})
    outer = make_wpistruct_from_schema(
        "Outer", "uint16 samples[2]; Inner children[2]", nested={"Inner": inner}
    )
    value = outer((1, 2), (inner(3), inner(4)))
    assert wpistruct.unpack(outer, wpistruct.pack(value)) == value


def test_generated_empty_schema_and_float_aliases():
    empty = make_wpistruct_from_schema("Empty", "", nested={})
    aliases = make_wpistruct_from_schema(
        "Aliases", "float32 first; float64 second", nested={}
    )
    assert wpistruct.get_size(empty) == 0
    assert wpistruct.unpack(empty, b"") == empty()
    assert wpistruct.get_schema(aliases) == "float32 first; float64 second"
    assert wpistruct.unpack(aliases, wpistruct.pack(aliases(1.5, 2.5))) == aliases(1.5, 2.5)


def test_generated_identifier_collision_is_deterministic():
    generated = make_wpistruct_from_schema(
        "pkg::Collision", "uint8 class; uint8 class_", nested={}
    )
    assert [field.name for field in dataclasses.fields(generated)] == ["class_", "class_2"]
    assert [field.python_name for field in generated.__wpistruct_descriptor__.fields] == [
        "class_",
        "class_2",
    ]


def test_generated_unknown_enum_is_typed():
    generated = make_wpistruct_from_schema(
        "ModeValue", "enum {OFF=0,AUTO=1} uint8 mode", nested={}
    )
    value = wpistruct.unpack(generated, b"\x07")
    assert isinstance(value.mode, generated.__dataclass_fields__["mode"].type)
    assert value.mode.name == "UNKNOWN_7"
    assert value.mode.value == 7


def test_generated_type_outlives_registry():
    registry = StructTypeRegistry(())
    generated = registry.add_schema("Value", "uint8 value")
    del registry
    gc.collect()
    assert wpistruct.unpack(generated, b"\x07") == generated(7)
    assert wpistruct.pack(generated(8)) == b"\x08"
```

- [ ] **Step 3: Write failing registry ordering and conflict tests**

Add:

```python
def test_registry_requires_nested_type_first():
    registry = StructTypeRegistry(())
    with pytest.raises(ValueError, match="Inner.*not registered"):
        registry.add_schema("Outer", "Inner value")


def test_registry_duplicate_and_conflict_behavior():
    registry = StructTypeRegistry(())
    first = registry.add_schema("Value", "int32 value;")
    assert registry.add_schema("Value", " int32 value ") is first
    with pytest.raises(ValueError, match="conflicting schema for Value"):
        registry.add_schema("Value", "uint32 value")


def test_registry_malformed_schema_is_distinct_error():
    with pytest.raises(InvalidStructSchema, match="expected identifier"):
        StructTypeRegistry(()).add_schema("Bad", "int32 [2]")
```

Add exact supplied-type precedence and duplicate-name tests:

```python
@wpistruct.make_wpistruct(name="Supplied")
@dataclasses.dataclass
class Supplied:
    value: wpistruct.int32


@wpistruct.make_wpistruct(name="Supplied")
@dataclasses.dataclass
class OtherSupplied:
    value: wpistruct.uint32


def test_registry_supplied_type_lookup_and_precedence():
    registry = StructTypeRegistry((Supplied,))
    assert registry.get("Supplied") is Supplied
    assert registry.add_schema("Supplied", "uint32 incompatible") is Supplied


def test_registry_rejects_duplicate_supplied_name_eagerly():
    with pytest.raises(ValueError, match="duplicate supplied struct type Supplied"):
        StructTypeRegistry((Supplied, OtherSupplied))


@wpistruct.make_wpistruct(name="Child")
@dataclasses.dataclass
class Child:
    value: wpistruct.uint8


@wpistruct.make_wpistruct(name="Parent")
@dataclasses.dataclass
class Parent:
    child: Child


def test_registry_seeds_supplied_nested_schemas_child_first():
    registry = StructTypeRegistry((Child, Parent))
    wrapper = registry.add_schema("Wrapper", "Parent parent")
    assert wpistruct.unpack(wrapper, wpistruct.pack(wrapper(Parent(Child(3))))) == wrapper(
        Parent(Child(3))
    )
```

- [ ] **Step 4: Run generated-schema tests and verify the module is absent**

```bash
python -m pytest subprojects/robotpy-wpiutil/tests/test_struct_schema.py -vv
```

Expected: collection fails because `wpiutil.wpistruct._schema` does not exist.

- [ ] **Step 5: Implement schema-to-annotation generation**

In `_schema.py`:

- Parse/add through the task-1 `SchemaDatabase`.
- Reject a descriptor that remains invalid immediately after `add_schema()`.
- Resolve nested `struct_name` values from the exact-name `nested` mapping.
- Map primitives to existing sized markers, `float`, `double`, `char`, and `Annotated[str, CharArray(n)]`.
- Create fixed tuple annotations for non-char arrays.
- Create one generated `IntEnum` per enum field, using a sanitized `<Struct><Field>` class name and preserving aliases.
- Add `BitField` and enum storage metadata with `Annotated`.
- Sanitize class/field identifiers by appending `_` for Python keywords/invalid identifiers and numeric suffixes for collisions.
- Create the mutable class with `dataclasses.make_dataclass()` and pass it to `compile_wpistruct()` with the original schema as `schema_override`.

- [ ] **Step 6: Implement `StructTypeRegistry`**

The constructor validates every supplied type with `wpistruct.get_type_name()`, rejects two different classes with one name, and seeds native nested schemas in `for_each_nested()` callback order. `add_schema()`:

- returns a supplied type without replacing it;
- translates parser errors to `InvalidStructSchema`;
- rejects unresolved nested Python classes;
- compares duplicate descriptors semantically;
- caches generated types and descriptors;
- retains all databases/classes through generated `WPIStruct` closures.

- [ ] **Step 7: Format and run all robotpy-wpiutil tests**

```bash
black subprojects/robotpy-wpiutil/wpiutil/wpistruct/_schema.py \
  subprojects/robotpy-wpiutil/tests/test_struct_schema.py
./rdev.sh develop robotpy-wpiutil
python subprojects/robotpy-wpiutil/tests/run_tests.py
```

Expected: all robotpy-wpiutil tests pass, including its native fixture installation.

- [ ] **Step 8: Commit schema-generated dataclasses**

```bash
git add subprojects/robotpy-wpiutil/wpiutil/wpistruct/_schema.py \
  subprojects/robotpy-wpiutil/wpiutil/wpistruct/_compiler.py \
  subprojects/robotpy-wpiutil/wpiutil/wpistruct/dataclass.py \
  subprojects/robotpy-wpiutil/tests/test_struct_schema.py
git commit -m "feat(wpiutil): generate wpistruct dataclasses from schemas"
```

---

### Task 6: Add `iter_auto()` primitive decoding and entry tracking

**Files:**
- Create: `subprojects/robotpy-wpilog/wpilog/_datalog.py`
- Modify: `subprojects/robotpy-wpilog/semiwrap/DataLogReader.yml`
- Create: `subprojects/robotpy-wpilog/tests/test_datalog_reader_auto.py`

**Interfaces:**
- Produces public `DataLogReader.iter_auto(*struct_types)`.
- Produces internal `_datalog._iter_auto(reader, struct_types: tuple[type, ...]) -> Iterator[tuple[DataLogRecord, StartRecordData | None, object]]`.
- Keeps native `DataLogReader.__iter__()` unchanged.
- Task 7 extends `_decode_value()` with struct schemas/values through Task 5 `StructTypeRegistry`.

- [ ] **Step 1: Write failing primitive dispatch tests**

Create `test_datalog_reader_auto.py` with a writer helper and parameterized cases:

```python
from pathlib import Path

import pytest
import wpilog


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
```

Add low-level entries for `json`, `raw`, and an unknown advertised type and assert `str`, `bytes`, and `bytes` respectively.

- [ ] **Step 2: Write failing lifecycle tests**

Use one `DataLogWriter` to create interleaved entries. Call `finish(entry_a)`, then `start()` the same name again to exercise the writer's entry-ID reuse. Assert data order, corresponding names/types, finish removal, and initial metadata. Add `append_raw(999, ...)` to assert orphan data yields `(record, None, bytes)`.

Also assert:

```python
def test_normal_reader_iteration_is_unchanged(log_path):
    values = list(wpilog.DataLogReader(str(log_path)))
    assert values
    assert all(isinstance(record, wpilog.DataLogRecord) for record in values)
```

- [ ] **Step 3: Run the tests and verify `iter_auto` is absent**

```bash
python -m pytest subprojects/robotpy-wpilog/tests/test_datalog_reader_auto.py -vv
```

Expected: `AttributeError: 'DataLogReader' object has no attribute 'iter_auto'`.

- [ ] **Step 4: Implement Python entry tracking and primitive dispatch**

Create `_datalog.py` with:

```python
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


def _iter_auto(reader, struct_types):
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
```

For Task 6, `_decode_value()` dispatches `_GETTERS` and returns raw bytes for all remaining types. Import `StructTypeRegistry` now so duplicate supplied types are validated eagerly even before Task 7's struct decoding.

- [ ] **Step 5: Bind the public method without changing `__iter__`**

Append a `.def("iter_auto", ...)` to `cls_DataLogReader` in `DataLogReader.yml` after the existing `__iter__` definition. Pass the native reader object plus the `py::args` tuple to:

```cpp
py::module_::import("wpilog._datalog").attr("_iter_auto")(self, structTypes)
```

Use `py::keep_alive<0, 1>()`. Do not subclass or replace `wpilog.DataLogReader` in `__init__.py`.

- [ ] **Step 6: Build and run primitive iterator tests**

```bash
black subprojects/robotpy-wpilog/wpilog/_datalog.py \
  subprojects/robotpy-wpilog/tests/test_datalog_reader_auto.py
./rdev.sh develop robotpy-wpilog
python -m pytest subprojects/robotpy-wpilog/tests/test_datalog_reader_auto.py -vv
```

Expected: primitive, lifecycle, and compatibility tests pass.

- [ ] **Step 7: Commit primitive automatic iteration**

```bash
git add subprojects/robotpy-wpilog/wpilog/_datalog.py \
  subprojects/robotpy-wpilog/semiwrap/DataLogReader.yml \
  subprojects/robotpy-wpilog/tests/test_datalog_reader_auto.py
git commit -m "feat(wpilog): add automatic primitive iteration"
```

---

### Task 7: Decode registered and generated structs in `iter_auto()`

**Files:**
- Modify: `subprojects/robotpy-wpilog/wpilog/_datalog.py`
- Modify: `subprojects/robotpy-wpilog/tests/test_datalog_reader_auto.py`
- Create: `subprojects/robotpy-wpimath/tests/geometry/test_datalog_struct.py`

**Interfaces:**
- Consumes: Task 5 `StructTypeRegistry`, `InvalidStructSchema`, and standard `wpistruct.unpack*()`.
- Completes `iter_auto()` schema and struct behavior.
- Schema names accepted: `/.schema/struct:<name>` and `NT:/.schema/struct:<name>`.

- [ ] **Step 1: Add a known struct and failing registered/generated tests**

At the top of `test_datalog_reader_auto.py`, define:

```python
import dataclasses
from wpiutil import wpistruct


@wpistruct.make_wpistruct(name="Reading")
@dataclasses.dataclass
class Reading:
    i: wpistruct.int32 = 0
    j: wpistruct.int32 = 0
```

Write a log with `wpilog.StructLogEntry(log, "/reading", Reading)` and assert:

- `iter_auto(Reading)` yields the schema record with `value is Reading` and the data record with `Reading(i, j)`.
- `iter_auto()` yields a generated dataclass type from the schema record and an instance of that exact type from the data record.
- A `StructArrayLogEntry` yields a list for both registered and generated paths.
Add a reuse test after the generated read:

```python
def test_iter_auto_generated_type_is_reusable(tmp_path):
    source = tmp_path / "source.wpilog"
    with wpilog.DataLogWriter(str(source)) as log:
        wpilog.StructLogEntry(log, "/reading", Reading).append(Reading(1, 2), 10)

    source_values = _read_auto(source)
    generated = next(value for _, entry, value in source_values if entry.type == "structschema")
    instance = next(value for _, entry, value in source_values if entry.type == "struct:Reading")

    destination = tmp_path / "destination.wpilog"
    with wpilog.DataLogWriter(str(destination)) as log:
        wpilog.StructLogEntry(log, "/copy", generated).append(instance, 20)

    copied = [
        value
        for _, entry, value in _read_auto(destination, generated)
        if entry.type == "struct:Reading"
    ]
    assert copied == [instance]
```

Add the native-capsule integration test to `subprojects/robotpy-wpimath/tests/geometry/test_datalog_struct.py`, where `Pose2d` is always available and the test runs in wpimath CI rather than being skipped:

```python
from pathlib import Path

import wpilog
from wpimath.geometry import Pose2d, Rotation2d


def test_iter_auto_supplied_native_pose2d(tmp_path: Path):
    pose = Pose2d(1.0, 2.0, Rotation2d())
    path = tmp_path / "native-struct.wpilog"
    with wpilog.DataLogWriter(str(path)) as log:
        wpilog.StructLogEntry(log, "/pose", Pose2d).append(pose, 10)

    decoded = [
        value
        for _, entry, value in wpilog.DataLogReader(str(path)).iter_auto(Pose2d)
        if entry is not None and entry.type == "struct:Pose2d"
    ]
    assert decoded == [pose]
```

Do not use `pytest.importorskip()` here. `robotpy-wpilog` precedes `robotpy-wpimath` in the workspace build order, and locating this test in the wpimath suite guarantees the native type is present in CI.

- [ ] **Step 2: Add nested and single-pass error tests**

Define a nested authored struct so the writer emits child schema before parent; assert generated nesting works. Then use low-level APIs:

```python
with wpilog.DataLogWriter(str(path)) as log:
    entry = log.start("/value", "struct:Late", "", 1)
    log.append_raw(entry, b"\x01", 2)
    log.add_schema("struct:Late", "structschema", "uint8 value", 3)
```

Assert iteration raises `ValueError` at timestamp 2 with entry/type context. Add parent-schema-before-child and malformed-schema-then-value cases. The malformed schema record itself must yield its original string before the later value raises.

- [ ] **Step 3: Add duplicate, precedence, and schema-name tests**

Test:

- whitespace/semicolon-equivalent duplicate schema records return the same generated class;
- conflicting duplicate schema records raise `ValueError`;
- supplied `Reading` takes precedence over a logged schema with the same name;
- two different supplied classes named `Reading` raise when `iter_auto()` is called, before consuming the generator;
- `NT:/.schema/struct:Reading` is recognized;
- a `structschema` entry with another name yields its schema string without registration.

Create duplicate schema records by starting `/.schema/struct:Name`, appending schema text, finishing it, and starting the same name again; `DataLog.add_schema()` intentionally suppresses duplicates and cannot exercise this policy.

- [ ] **Step 4: Run struct tests and verify values still fall back to bytes**

```bash
python -m pytest subprojects/robotpy-wpilog/tests/test_datalog_reader_auto.py -vv
```

Expected: primitive tests pass; new schema/struct assertions fail because `_decode_value()` still returns raw bytes.

- [ ] **Step 5: Implement schema-name and struct-type parsing**

Add helpers:

```python
_SCHEMA_PREFIX = "/.schema/struct:"
_STRUCT_PREFIX = "struct:"


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
```

- [ ] **Step 6: Implement schema and struct decoding**

In `_decode_value()`:

- Decode `structschema` bytes to text using the existing string getter.
- Return the text unchanged when the entry name is not recognized.
- Call `registry.add_schema()` for recognized schema names.
- Catch only `InvalidStructSchema` and return the original text; allow unresolved nesting/conflicts to propagate.
- For `struct:<name>`, require `registry.get(name)` and raise contextual `ValueError` when absent.
- Use `wpistruct.unpack()` for scalars and `unpack_array()` for arrays.
- Keep primitive dispatch before unknown raw fallback.

Ensure `_iter_auto()` constructs `StructTypeRegistry` before returning `_iter_records()` so duplicate supplied types fail at method-call time rather than first `next()`.

- [ ] **Step 7: Run wpiutil, wpilog, and wpimath project suites**

```bash
black subprojects/robotpy-wpilog/wpilog/_datalog.py \
  subprojects/robotpy-wpilog/tests/test_datalog_reader_auto.py \
  subprojects/robotpy-wpimath/tests/geometry/test_datalog_struct.py
./rdev.sh develop --stop-at robotpy-wpimath
python subprojects/robotpy-wpiutil/tests/run_tests.py
python subprojects/robotpy-wpilog/tests/run_tests.py
python subprojects/robotpy-wpimath/tests/run_tests.py
```

Expected: all three suites pass, including the non-skipped native `Pose2d` integration test.

- [ ] **Step 8: Commit struct automatic decoding**

```bash
git add subprojects/robotpy-wpilog/wpilog/_datalog.py \
  subprojects/robotpy-wpilog/tests/test_datalog_reader_auto.py \
  subprojects/robotpy-wpimath/tests/geometry/test_datalog_struct.py
git commit -m "feat(wpilog): decode registered and logged structs"
```

---

### Task 8: Update datalog examples and perform final verification

**Files:**
- Create: `examples/datalog/datalog_struct.py`
- Modify: `examples/datalog/writelog.py`
- Modify: `examples/datalog/printlog.py`

**Interfaces:**
- Demonstrates `DataLogReader.iter_auto()` with no supplied type and with a predefined `make_wpistruct` type.
- Produces a writer output that can be consumed directly by both reader modes.

- [ ] **Step 1: Add the shared example struct**

Create `examples/datalog/datalog_struct.py`:

```python
import dataclasses

from wpiutil import wpistruct


@wpistruct.make_wpistruct(name="ExampleRecord")
@dataclasses.dataclass
class ExampleRecord:
    i: wpistruct.int32 = 0
    j: wpistruct.int32 = 0
```

- [ ] **Step 2: Write the example struct in `writelog.py`**

Import `ExampleRecord`, create `wpilog.StructLogEntry(datalog, "/record", ExampleRecord)`, and append at least `ExampleRecord(1, 2)` and `ExampleRecord(3, 4)`. Keep the existing primitive examples.

- [ ] **Step 3: Replace manual decoding in `printlog.py` with `iter_auto()`**

Add `--predefined` and select types with:

```python
struct_types = (ExampleRecord,) if args.predefined else ()

for record, entry, value in reader.iter_auto(*struct_types):
    timestamp = record.get_timestamp() / 1_000_000
    name = entry.name if entry is not None else f"entry:{record.get_entry()}"
    advertised_type = entry.type if entry is not None else "unknown"
    print(f"{name} [{advertised_type}] [{timestamp}] {value!r}")
```

The default demonstrates generated classes; `--predefined` demonstrates caller registration.

- [ ] **Step 4: Format all changed Python files**

```bash
black subprojects/robotpy-wpiutil/wpiutil/wpistruct \
  subprojects/robotpy-wpiutil/tests/test_struct.py \
  subprojects/robotpy-wpiutil/tests/test_schema_bridge.py \
  subprojects/robotpy-wpiutil/tests/test_struct_annotations.py \
  subprojects/robotpy-wpiutil/tests/test_struct_schema.py \
  subprojects/robotpy-wpilog/wpilog/_datalog.py \
  subprojects/robotpy-wpilog/tests/test_datalog_reader_auto.py \
  subprojects/robotpy-wpimath/tests/geometry/test_datalog_struct.py \
  examples/datalog
```

- [ ] **Step 5: Run all three complete subproject test launchers**

```bash
python subprojects/robotpy-wpiutil/tests/run_tests.py
python subprojects/robotpy-wpilog/tests/run_tests.py
python subprojects/robotpy-wpimath/tests/run_tests.py
```

Expected: all three commands exit 0.

- [ ] **Step 6: Exercise both example modes end to end**

```bash
rm -f /tmp/iter-auto.wpilog
python examples/datalog/writelog.py /tmp/iter-auto.wpilog
python examples/datalog/printlog.py /tmp/iter-auto.wpilog
python examples/datalog/printlog.py --predefined /tmp/iter-auto.wpilog
```

Expected: both print commands show `/record` values; default values use a generated `ExampleRecord` class and `--predefined` values use `datalog_struct.ExampleRecord`.

- [ ] **Step 7: Inspect final diff and run whitespace checks**

```bash
git diff --check
git status --short
git diff --stat
```

Expected: no whitespace errors and only planned source, binding, test, example, and generated import files are modified. Do not commit build directories or semiwrap generated module/trampoline directories.

- [ ] **Step 8: Commit examples and final integration**

```bash
git add examples/datalog
git commit -m "docs: demonstrate automatic wpilog struct decoding"
```
