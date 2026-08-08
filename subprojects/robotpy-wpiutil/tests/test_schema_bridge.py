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


def test_schema_database_find():
    db = SchemaDatabase()
    assert db.find("Value") is None

    added = db.add("Value", "uint8 value")
    found = db.find("Value")

    assert found is not None
    assert found.name == added.name
    assert found.schema == added.schema
    assert found.size == added.size


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
