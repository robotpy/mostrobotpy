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


def test_legacy_singleton_tuple_remains_an_array():
    @wpistruct.make_wpistruct
    @dataclasses.dataclass
    class SingletonTuple:
        value: tuple[wpistruct.uint8]

    value = SingletonTuple((7,))
    assert wpistruct.get_schema(SingletonTuple) == "uint8 value[1]"
    assert wpistruct.pack(value) == b"\x07"
    assert wpistruct.unpack(SingletonTuple, b"\x08") == SingletonTuple((8,))


def test_legacy_annotated_metadata_uses_base_type():
    @wpistruct.make_wpistruct
    @dataclasses.dataclass
    class AnnotatedValue:
        value: Annotated[int, "application metadata"]

    value = AnnotatedValue(7)
    assert wpistruct.get_schema(AnnotatedValue) == "int32 value"
    assert wpistruct.unpack(AnnotatedValue, wpistruct.pack(value)) == value


def test_compile_failure_does_not_partially_decorate_class():
    from wpiutil.wpistruct._compiler import compile_wpistruct

    @dataclasses.dataclass
    class InvalidSchema:
        value: int

    with pytest.raises(ValueError, match="expected identifier"):
        compile_wpistruct(InvalidSchema, "InvalidSchema", schema_override="int32 [2]")

    assert "WPIStruct" not in InvalidSchema.__dict__
    assert "__wpistruct_descriptor__" not in InvalidSchema.__dict__


def test_compiler_attaches_parsed_layout_metadata():
    assert Legacy.__wpistruct_descriptor__ == wpistruct.StructLayout(
        type_name="Legacy",
        schema="int32 count; uint16 values[2]",
        size=8,
        fields=(
            wpistruct.StructFieldLayout(
                schema_name="count",
                python_name="count",
                type_name="int32",
                offset=0,
                size=4,
                array_size=1,
                bit_width=32,
                bit_shift=0,
                bit_mask=0xFFFFFFFF,
                enum_values=(),
                nested_type=None,
            ),
            wpistruct.StructFieldLayout(
                schema_name="values",
                python_name="values",
                type_name="uint16",
                offset=4,
                size=2,
                array_size=2,
                bit_width=16,
                bit_shift=0,
                bit_mask=0xFFFF,
                enum_values=(),
                nested_type=None,
            ),
        ),
    )
