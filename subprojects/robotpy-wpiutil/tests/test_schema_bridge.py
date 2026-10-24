import gc
import math
import subprocess
import sys

import pytest

from wpiutil._wpiutil._schema import SchemaDatabase, pack_schema, unpack_schema


def test_schema_bridge_exposes_only_codec_support():
    from wpiutil._wpiutil import _schema

    database = SchemaDatabase()
    descriptor = database.add("Value", "uint8 value")
    assert not hasattr(database, "stage")
    assert not hasattr(database, "find")
    assert not hasattr(_schema, "SchemaFieldDescriptor")
    for attribute in (
        "name",
        "schema",
        "fields",
        "get_name",
        "get_schema",
        "get_fields",
    ):
        assert not hasattr(descriptor, attribute)
    assert descriptor.is_valid
    assert descriptor.size == 1
    assert pack_schema(descriptor, (7,)) == b"\x07"
    assert unpack_schema(descriptor, b"\x08") == (8,)


def test_schema_database_accepts_utf8_identifiers():
    database = SchemaDatabase()
    nested = database.add("温度类型", "uint16 变量")
    descriptor = database.add("UnicodePacket", "int32 é; 温度类型 π")
    values = (-2, pack_schema(nested, (0x1234,)))
    encoded = b"\xfe\xff\xff\xff\x34\x12"
    assert descriptor.size == 6
    assert pack_schema(descriptor, values) == encoded
    assert unpack_schema(descriptor, encoded) == values


def test_schema_descriptor_nested_delayed_validity():
    db = SchemaDatabase()
    outer = db.add("Outer", "Inner value")
    assert not outer.is_valid
    with pytest.raises(ValueError, match="descriptor Outer is not valid"):
        _ = outer.size

    db.add("Inner", "int32 value")
    assert outer.is_valid
    assert outer.size == 4
    assert pack_schema(outer, (b"\x07\0\0\0",)) == b"\x07\0\0\0"


def test_schema_descriptor_parse_error():
    db = SchemaDatabase()
    with pytest.raises(ValueError, match="expected identifier"):
        db.add("Bad", "int32 [2]")


def test_schema_descriptor_retains_database():
    desc = SchemaDatabase().add("Value", "uint8 value")
    gc.collect()
    assert desc.size == 1
    assert unpack_schema(desc, pack_schema(desc, (7,))) == (7,)


def test_schema_database_add_all_completes_retained_dependency_chain():
    database = SchemaDatabase()
    candidate = database.add("Outer", "Middle value")
    assert not candidate.is_valid
    database.add_all([("Inner", "uint8 value"), ("Middle", "Inner value")])
    assert candidate.is_valid
    assert candidate.size == 1
    assert unpack_schema(candidate, pack_schema(candidate, (b"\x07",))) == (b"\x07",)


def test_schema_database_add_all_rolls_back_malformed_batch():
    database = SchemaDatabase()
    retained = database.add("Outer", "Inner value")
    existing = database.add("Existing", "uint8 value")
    with pytest.raises(ValueError, match="expected identifier"):
        database.add_all([("Inner", "uint16 value"), ("Malformed", "int32 [2]")])

    assert not retained.is_valid
    assert existing.size == 1
    assert pack_schema(existing, (7,)) == b"\x07"
    # Different definitions must still be accepted after rollback.
    database.add_all([("Inner", "uint32 value"), ("Malformed", "uint8 value")])
    assert retained.is_valid
    assert retained.size == 4
    assert pack_schema(retained, (b"\x07\0\0\0",)) == b"\x07\0\0\0"


def test_schema_database_add_all_rolls_back_conflicting_batch():
    database = SchemaDatabase()
    retained = database.add("Outer", "Parent value")
    existing = database.add("Existing", "uint8 value")
    with pytest.raises(ValueError, match="conflicting schema for Existing"):
        database.add_all(
            [
                ("Inner", "uint16 value"),
                ("Existing", "uint32 value"),
                ("Parent", "Inner value"),
            ]
        )

    assert not retained.is_valid
    assert existing.size == 1
    assert pack_schema(existing, (7,)) == b"\x07"
    database.add_all([("Inner", "uint32 value"), ("Parent", "Inner value")])
    assert retained.is_valid
    assert retained.size == 4
    assert pack_schema(retained, (b"\x07\0\0\0",)) == b"\x07\0\0\0"


def test_schema_database_add_all_candidate_outlives_database():
    database = SchemaDatabase()
    candidate = database.add("Outer", "Inner value")
    database.add_all([("Inner", "uint8 value")])
    del database
    gc.collect()
    assert candidate.is_valid
    assert candidate.size == 1
    assert unpack_schema(candidate, pack_schema(candidate, (b"\x07",))) == (b"\x07",)


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
    assert duplicate.size == original.size == 4
    assert pack_schema(duplicate, (1.5,)) == pack_schema(original, (1.5,))
    with pytest.raises(ValueError, match="conflicting schema for Value"):
        db.add("Value", "double value")
    assert original.size == 4
    assert pack_schema(original, (1.5,)) == b"\x00\x00\xc0?"


@pytest.mark.parametrize(
    ("original_schema", "conflicting_schema"),
    [
        ("int16 prefix:2; bool value", "int16 prefix:2; bool value:1"),
        ("uint8 value", "uint8 value:7"),
    ],
)
def test_schema_database_rejects_different_bitfield_layouts(
    original_schema, conflicting_schema
):
    database = SchemaDatabase()
    database.add("Packet", original_schema)
    with pytest.raises(ValueError, match="conflicting schema for Packet"):
        database.add("Packet", conflicting_schema)


def test_failed_semantic_add_does_not_create_descriptor():
    db = SchemaDatabase()
    with pytest.raises(ValueError, match="duplicate field value"):
        db.add("Bad", "int8 value; int16 value")
    recovered = db.add("Bad", "int8 value")
    assert recovered.is_valid
    assert recovered.size == 1
    assert pack_schema(recovered, (-2,)) == b"\xfe"


def test_failed_placeholder_completion_is_transactional():
    db = SchemaDatabase()
    outer = db.add("Outer", "Inner value")
    with pytest.raises(ValueError, match="circular struct reference"):
        db.add("Inner", "Outer value")
    assert not outer.is_valid
    inner = db.add("Inner", "int32 value")
    assert inner.is_valid
    assert inner.size == 4
    assert outer.is_valid
    assert outer.size == 4
    assert pack_schema(outer, (pack_schema(inner, (7,)),)) == b"\x07\0\0\0"


def test_schema_layout_overflow_is_rejected_before_publication():
    db = SchemaDatabase()
    with pytest.raises(
        ValueError,
        match=r"unsafe schema layout for Overflow: field values storage extent exceeds platform limits",
    ):
        db.add("Overflow", "uint64 values[2305843009213693952]")
    recovered = db.add("Overflow", "uint8 value")
    assert recovered.is_valid
    assert recovered.size == 1
    assert pack_schema(recovered, (7,)) == b"\x07"


def test_nested_schema_layout_overflow_is_rejected_transactionally():
    db = SchemaDatabase()
    outer = db.add("Outer", "Inner values[2305843009213693952]")
    assert not outer.is_valid
    with pytest.raises(
        ValueError,
        match=r"unsafe schema layout for Outer: field values storage extent exceeds platform limits",
    ):
        db.add("Inner", "uint64 value")
    assert not outer.is_valid
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
        ("float32 value", 1.5, b"\x00\x00\xc0?"),
        ("double value", 1.5, b"\x00\x00\x00\x00\x00\x00\xf8?"),
        ("float64 value", 1.5, b"\x00\x00\x00\x00\x00\x00\xf8?"),
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
    assert pack_schema(desc, (7,)) == b"\x07"
    assert unpack_schema(desc, b"\x08") == (8,)
    with pytest.raises(TypeError, match="samples.*must be an integer"):
        pack_schema(desc, ((7,),))
    equivalent = db.add("Packet", "uint8 samples")
    assert pack_schema(equivalent, (7,)) == b"\x07"


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
        self.other = None

    def __len__(self):
        if self.other is None:
            self.other = self.db.add("Other", "uint64 a; uint64 b; uint64 c; uint64 d")
        return 1

    def __getitem__(self, index):
        if index == 0:
            return 7
        raise IndexError


db = SchemaDatabase()
desc = db.add("Value", "uint8 value")
values = MutatingValues(db)
assert pack_schema(desc, values) == b"\\x07"
assert values.other.is_valid
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
    [("int8 value", 128, r"-128.*127"), ("uint8 value", 256, r"0.*255")],
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
    [("int8 value:4", -8, 7), ("uint64 value:63", 0, 2**63 - 1)],
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
    [(math.inf, b"\x00\x00\x80\x7f"), (-math.inf, b"\x00\x00\x80\xff")],
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
        ("int16 a:2; bool b:1; bool c:1; uint16 d:5", (-1, True, False, 17), 2),
    ],
)
def test_schema_bitfield_placement(schema, values, size):
    desc = SchemaDatabase().add("Bits", schema)
    assert desc.size == size
    assert unpack_schema(desc, pack_schema(desc, values)) == values
