import gc
import math
import subprocess
import sys

import pytest

from wpiutil._wpiutil._schema import SchemaDatabase, pack_schema, unpack_schema


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


def test_schema_database_find():
    db = SchemaDatabase()
    assert db.find("Value") is None

    added = db.add("Value", "uint8 value")
    found = db.find("Value")

    assert found is not None
    assert found.name == added.name
    assert found.schema == added.schema
    assert found.size == added.size


def test_schema_descriptor_preserves_declaration_shape_metadata():
    desc = SchemaDatabase().add(
        "Shapes",
        "uint8 scalar; uint8 singleton[1]; uint8 full_width:8; "
        "enum {} uint8 empty_mode",
    )

    scalar, singleton, full_width, empty_mode = desc.fields
    assert not scalar.is_array
    assert not scalar.is_bit_field
    assert not scalar.is_enum
    assert singleton.is_array
    assert not singleton.is_bit_field
    assert not singleton.is_enum
    assert not full_width.is_array
    assert full_width.is_bit_field
    assert not full_width.is_enum
    assert not empty_mode.is_array
    assert not empty_mode.is_bit_field
    assert empty_mode.is_enum


def test_schema_database_stages_without_mutating_source():
    source = SchemaDatabase()
    source.add("First", "uint8 value")

    staged = source.stage("Second", "First nested")

    assert source.find("Second") is None
    assert staged.find("First").size == 1
    assert staged.find("Second").size == 1

    duplicate_stage = source.stage("First", " uint8 value; ")
    duplicate_stage.add("Third", "uint16 value")
    assert source.find("Third") is None
    assert duplicate_stage.find("Third").size == 2


def test_schema_database_stage_rejects_contextually_different_bool_bitfield():
    database = SchemaDatabase()
    database.add("Packet", "int16 prefix:2; bool value")

    with pytest.raises(ValueError, match="conflicting schema for Packet"):
        database.stage("Packet", "int16 prefix:2; bool value:1")


def test_schema_database_stage_rejects_non_full_width_integer_bitfield():
    database = SchemaDatabase()
    database.add("Packet", "uint8 value")

    with pytest.raises(ValueError, match="conflicting schema for Packet"):
        database.stage("Packet", "uint8 value:7")


@pytest.mark.parametrize(
    ("existing_schema", "candidate_schema", "attribute", "expected"),
    [
        ("uint8 value", "uint8 value[1]", "is_array", True),
        ("uint8 value[1]", "uint8 value", "is_array", False),
        ("uint8 value", "uint8 value:8", "is_bit_field", True),
        ("int16 value", "int16 value:16", "is_bit_field", True),
        ("uint32 value:32", "uint32 value", "is_bit_field", False),
        ("int64 value", "int64 value:64", "is_bit_field", True),
        ("uint8 value", "enum {} uint8 value", "is_enum", True),
    ],
)
def test_equivalent_stage_uses_candidate_declaration_shape(
    existing_schema, candidate_schema, attribute, expected
):
    database = SchemaDatabase()
    source = database.add("Packet", existing_schema)

    staged = database.stage("Packet", candidate_schema)
    candidate = staged.find("Packet")

    assert candidate.schema == candidate_schema
    assert source.schema == existing_schema
    assert database.find("Packet").schema == existing_schema
    assert getattr(candidate.fields[0], attribute) is expected
    assert getattr(source.fields[0], attribute) is not expected
    assert getattr(database.find("Packet").fields[0], attribute) is not expected


def test_schema_descriptor_arrays_chars_and_enums():
    db = SchemaDatabase()
    desc = db.add(
        "Complete",
        "char letter; char text[4]; int16 samples[3]; " "enum {OFF=0, ON=2} uint8 mode",
    )

    assert desc.size == 12
    assert [field.name for field in desc.fields] == [
        "letter",
        "text",
        "samples",
        "mode",
    ]
    assert [field.type for field in desc.fields] == [
        "char",
        "char",
        "int16",
        "uint8",
    ]
    assert [field.offset for field in desc.fields] == [0, 1, 5, 11]
    assert [field.size for field in desc.fields] == [1, 1, 2, 1]
    assert [field.array_size for field in desc.fields] == [1, 4, 3, 1]
    assert desc.fields[3].enum_values == [("OFF", 0), ("ON", 2)]


@pytest.mark.parametrize(
    ("schema_type", "canonical_type", "size"),
    [("float32", "float", 4), ("float64", "double", 8)],
)
def test_schema_descriptor_primitive_aliases(schema_type, canonical_type, size):
    db = SchemaDatabase()
    desc = db.add("Value", f"{schema_type} value")

    assert desc.size == size
    assert desc.fields[0].type == canonical_type
    assert desc.fields[0].size == size


@pytest.mark.parametrize(
    ("schema", "error"),
    [
        ("char value:1", "type char cannot be bitfield"),
        ("int8 value:9", "bit width 9 exceeds type size"),
        ("bool value:2", "bit width must be 1 for bool type"),
        ("Recursive value", "recursive struct reference"),
        ("int8 value; int16 value", "duplicate field value"),
    ],
)
def test_schema_descriptor_semantic_validation_errors(schema, error):
    db = SchemaDatabase()

    with pytest.raises(ValueError, match=error):
        db.add("Recursive", schema)


def test_schema_descriptor_duplicate_and_conflicting_definitions():
    db = SchemaDatabase()
    original = db.add("Value", "float value")

    duplicate = db.add("Value", "float32 value")
    assert duplicate.schema == original.schema
    assert duplicate.size == original.size

    with pytest.raises(ValueError, match="conflicting schema for Value"):
        db.add("Value", "double value")

    assert db.find("Value").schema == "float value"
    assert db.find("Value").size == 4


def test_failed_semantic_add_does_not_create_descriptor():
    db = SchemaDatabase()

    with pytest.raises(ValueError, match="duplicate field value"):
        db.add("Bad", "int8 value; int16 value")

    assert db.find("Bad") is None
    recovered = db.add("Bad", "int8 value")
    assert recovered.is_valid
    assert recovered.size == 1


def test_failed_placeholder_completion_is_transactional():
    db = SchemaDatabase()
    outer = db.add("Outer", "Inner value")
    inner_placeholder = db.find("Inner")
    assert inner_placeholder is not None
    assert not inner_placeholder.is_valid

    with pytest.raises(ValueError, match="circular struct reference"):
        db.add("Inner", "Outer value")

    assert not outer.is_valid
    assert not inner_placeholder.is_valid
    assert inner_placeholder.schema == ""

    inner = db.add("Inner", "int32 value")
    assert inner.is_valid
    assert inner.size == 4
    assert outer.is_valid
    assert outer.size == 4


def test_schema_layout_overflow_is_rejected_before_publication():
    db = SchemaDatabase()

    with pytest.raises(
        ValueError,
        match=(
            r"unsafe schema layout for Overflow: field values storage extent "
            r"exceeds platform limits"
        ),
    ):
        db.add("Overflow", "uint64 values[2305843009213693952]")

    assert db.find("Overflow") is None
    recovered = db.add("Overflow", "uint8 value")
    assert recovered.is_valid
    assert recovered.size == 1


def test_nested_schema_layout_overflow_is_rejected_transactionally():
    db = SchemaDatabase()
    outer = db.add("Outer", "Inner values[2305843009213693952]")
    inner_placeholder = db.find("Inner")
    assert inner_placeholder is not None
    assert not outer.is_valid
    assert not inner_placeholder.is_valid

    with pytest.raises(
        ValueError,
        match=(
            r"unsafe schema layout for Outer: field values storage extent "
            r"exceeds platform limits"
        ),
    ):
        db.add("Inner", "uint64 value")

    assert not outer.is_valid
    assert not inner_placeholder.is_valid
    assert inner_placeholder.schema == ""

    inner = db.add("Inner", "")
    assert inner.is_valid
    assert inner.size == 0
    assert outer.is_valid
    assert outer.size == 0


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


def test_schema_non_char_array_accepts_byte_sequences():
    desc = SchemaDatabase().add("Samples", "uint8 samples[2]")

    assert pack_schema(desc, (b"\x01\x02",)) == b"\x01\x02"
    assert pack_schema(desc, (bytearray(b"\x03\x04"),)) == b"\x03\x04"


def test_schema_singleton_array_uses_wpilib_scalar_semantics():
    db = SchemaDatabase()
    desc = db.add("Packet", "uint8 samples[1]")

    assert desc.schema == "uint8 samples[1]"
    assert desc.fields[0].array_size == 1
    assert pack_schema(desc, (7,)) == b"\x07"
    assert unpack_schema(desc, b"\x08") == (8,)

    with pytest.raises(TypeError, match="samples.*must be an integer"):
        pack_schema(desc, ((7,),))

    equivalent = db.add("Packet", "uint8 samples")
    assert equivalent.schema == "uint8 samples[1]"


def test_schema_nested_array_unpacks_exact_size_bytes():
    db = SchemaDatabase()
    db.add("Inner", "uint16 value")
    outer = db.add("Outer", "Inner nested[2]")

    assert unpack_schema(outer, b"\x01\x00\x02\x00") == ((b"\x01\x00", b"\x02\x00"),)


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


def test_schema_pack_pins_descriptor_during_sequence_reentrancy():
    script = """
from wpiutil._wpiutil._schema import SchemaDatabase, pack_schema


class MutatingValues:
    def __init__(self, db):
        self.db = db
        self.mutated = False

    def __len__(self):
        if not self.mutated:
            self.mutated = True
            self.db.add("Other", "uint64 a; uint64 b; uint64 c; uint64 d")
        return 1

    def __getitem__(self, index):
        if index == 0:
            return 7
        raise IndexError


db = SchemaDatabase()
desc = db.add("Value", "uint8 value")
assert pack_schema(desc, MutatingValues(db)) == b"\\x07"
assert db.find("Other").is_valid
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr


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


@pytest.mark.parametrize(
    ("schema", "value", "bounds"),
    [
        ("int8 value", 128, r"-128.*127"),
        ("uint8 value", 256, r"0.*255"),
    ],
)
def test_schema_integer_subclass_cannot_bypass_range_validation(schema, value, bounds):
    class LyingInt(int):
        def __lt__(self, other):
            return False

        def __gt__(self, other):
            return False

    desc = SchemaDatabase().add("Value", schema)

    with pytest.raises(ValueError, match=rf"value.*{bounds}"):
        pack_schema(desc, (LyingInt(value),))


@pytest.mark.parametrize(
    ("schema", "below_minimum", "above_maximum"),
    [
        ("int8 value", -(2**7) - 1, 2**7),
        ("int16 value", -(2**15) - 1, 2**15),
        ("int32 value", -(2**31) - 1, 2**31),
        ("int64 value", -(2**63) - 1, 2**63),
        ("uint8 value", -1, 2**8),
        ("uint16 value", -1, 2**16),
        ("uint32 value", -1, 2**32),
        ("uint64 value", -1, 2**64),
    ],
)
def test_schema_integer_rejects_one_past_limits(schema, below_minimum, above_maximum):
    desc = SchemaDatabase().add("Value", schema)

    with pytest.raises(ValueError, match="value.*must be between"):
        pack_schema(desc, (below_minimum,))
    with pytest.raises(ValueError, match="value.*must be between"):
        pack_schema(desc, (above_maximum,))


@pytest.mark.parametrize(
    ("schema", "minimum", "maximum"),
    [
        ("int8 value:4", -8, 7),
        ("uint64 value:63", 0, 2**63 - 1),
    ],
)
def test_schema_bitfield_enforces_exact_integer_limits(schema, minimum, maximum):
    desc = SchemaDatabase().add("Value", schema)

    for value in (minimum, maximum):
        assert unpack_schema(desc, pack_schema(desc, (value,))) == (value,)
    for value in (minimum - 1, maximum + 1):
        with pytest.raises(ValueError, match="value.*must be between"):
            pack_schema(desc, (value,))


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


def test_schema_float_rejects_finite_float32_overflow():
    desc = SchemaDatabase().add("Value", "float value")

    float32_max = float.fromhex("0x1.fffffep+127")
    assert pack_schema(desc, (float32_max,)) == b"\xff\xff\x7f\x7f"
    assert pack_schema(desc, (-float32_max,)) == b"\xff\xff\x7f\xff"

    outside = math.nextafter(float32_max, math.inf)
    for value in (outside, -outside, 1e300, -1e300):
        with pytest.raises(ValueError, match="value.*float32 range"):
            pack_schema(desc, (value,))


@pytest.mark.parametrize(
    ("value", "encoded"),
    [
        (math.inf, b"\x00\x00\x80\x7f"),
        (-math.inf, b"\x00\x00\x80\xff"),
    ],
)
def test_schema_float_preserves_infinities(value, encoded):
    desc = SchemaDatabase().add("Value", "float value")

    assert pack_schema(desc, (value,)) == encoded
    assert unpack_schema(desc, encoded) == (value,)


def test_schema_float_preserves_nan():
    desc = SchemaDatabase().add("Value", "float value")

    (unpacked,) = unpack_schema(desc, pack_schema(desc, (math.nan,)))
    assert math.isnan(unpacked)


@pytest.mark.parametrize(
    ("schema", "values", "size"),
    [
        ("int32 a:2; uint32 b:30", (-1, 100), 4),
        ("int32 a:2; int16 b:2", (-1, -2), 6),
        ("int8 a:4; int8 b:5", (-1, -2), 2),
        (
            "int16 a:2; bool b:1; bool c:1; uint16 d:5",
            (-1, True, False, 17),
            2,
        ),
    ],
)
def test_schema_bitfield_placement(schema, values, size):
    desc = SchemaDatabase().add("Bits", schema)
    assert desc.size == size
    assert unpack_schema(desc, pack_schema(desc, values)) == values
