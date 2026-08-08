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
