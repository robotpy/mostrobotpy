import array
import ctypes
import dataclasses
import re
import sys

import pytest

from wpiutil import wpistruct
from wpiutil.wpistruct._schema import make_wpistruct_from_schema
from wpiutil_test import module


class _PackReachedError(RuntimeError):
    pass


def _make_pack_probe_type(size):
    class PackProbe:
        def __init__(self, fail_on_call):
            self.fail_on_call = fail_on_call
            self.pack_calls = 0

    def pack(value):
        value.pack_calls += 1
        if value.pack_calls == value.fail_on_call:
            raise _PackReachedError("pack callback reached")
        return b"x" * size

    PackProbe.WPIStruct = wpistruct.StructDescriptor(
        typename=f"PackProbe{size}",
        schema=f"uint8 data[{size}]",
        size=size,
        pack=pack,
        pack_into=lambda value, destination: None,
        unpack=lambda buffer: None,
        for_each_nested=None,
    )
    return PackProbe


_PackProbe0 = _make_pack_probe_type(0)
_PackProbe2 = _make_pack_probe_type(2)
_PackProbe3 = _make_pack_probe_type(3)


class _ConstantLengthSequence:
    def __init__(self, length, item):
        self.length = length
        self.item = item

    def __len__(self):
        return self.length

    def __getitem__(self, index):
        if index != 0:
            raise IndexError
        return self.item


class _GrowingLengthSequence:
    def __init__(self, item):
        self.item = item
        self.length_calls = 0

    def __len__(self):
        self.length_calls += 1
        return self.length_calls

    def __getitem__(self, index):
        if index >= 2:
            raise IndexError
        return self.item


#
# Static serialization
#


# ensure that a type that doesn't work has a sane error message
def test_invalid_type():
    with pytest.raises(
        TypeError,
        match=re.escape("str is not struct serializable (does not have WPIStruct)"),
    ):
        wpistruct.get_schema(str)


def test_for_each_nested():
    l = []

    def _fn(*args):
        l.append(args)

    wpistruct.for_each_nested(module.ThingA, _fn)
    assert l == [("struct:ThingA", "uint8 value")]


def test_get_type_string():
    assert wpistruct.get_type_name(module.ThingA) == "ThingA"


def test_get_schema():
    assert wpistruct.get_schema(module.ThingA) == "uint8 value"


def test_get_size():
    assert wpistruct.get_size(module.ThingA) == 1


def test_pack():
    assert wpistruct.pack(module.ThingA(1)) == b"\x01"


def test_pack_array():
    assert wpistruct.pack_array([module.ThingA(1), module.ThingA(2)]) == b"\x01\x02"


@pytest.mark.parametrize(
    ("probe_type", "length"),
    [
        (
            _PackProbe3,
            ((1 << (ctypes.sizeof(ctypes.c_size_t) * 8)) - 1) // 3 + 2,
        ),
        (_PackProbe2, sys.maxsize // 2 + 1),
    ],
    ids=["size_t", "py_ssize_t"],
)
def test_pack_array_rejects_unrepresentable_total_before_packing(probe_type, length):
    item = probe_type(fail_on_call=1)
    values = _ConstantLengthSequence(length, item)

    with pytest.raises(OverflowError, match="packed array is too large"):
        wpistruct.pack_array(values)

    assert item.pack_calls == 0


def test_pack_array_uses_captured_length_for_packing_loop():
    item = _PackProbe3(fail_on_call=2)
    values = _GrowingLengthSequence(item)

    assert wpistruct.pack_array(values) == b"xxx"
    assert values.length_calls == 1
    assert item.pack_calls == 1


def test_pack_into():
    buf = bytearray(1)
    wpistruct.pack_into(module.ThingA(1), buf)
    assert buf == b"\x01"


def test_pack_into_err():
    buf = bytearray(2)
    with pytest.raises(ValueError, match=re.escape("buffer must be 1 bytes")):
        wpistruct.pack_into(module.ThingA(1), buf)


def test_pack_into_rejects_readonly_buffer():
    destination = b"\x00"

    with pytest.raises(BufferError, match="writable"):
        wpistruct.pack_into(module.ThingA(1), destination)

    assert destination == b"\x00"


def test_pack_into_rejects_noncontiguous_buffer_without_mutation():
    backing = bytearray(b"\xaa\xbb")
    destination = memoryview(backing)[::2]

    with pytest.raises(ValueError, match="buffer must be contiguous"):
        wpistruct.pack_into(module.ThingA(1), destination)

    assert backing == b"\xaa\xbb"


@pytest.mark.parametrize(
    "destination",
    [
        bytearray(1),
        memoryview(bytearray(1)),
        array.array("b", [0]),
        array.array("B", [0]),
    ],
)
def test_pack_into_accepts_contiguous_writable_byte_buffers(destination):
    wpistruct.pack_into(module.ThingA(7), destination)

    assert bytes(destination) == b"\x07"


def test_unpack():
    assert wpistruct.unpack(module.ThingA, b"\x01") == module.ThingA(1)


def test_unpack_array():
    assert wpistruct.unpack_array(module.ThingA, b"\x01\x02") == [
        module.ThingA(1),
        module.ThingA(2),
    ]


@pytest.mark.parametrize("buffer_type", [bytes, bytearray, memoryview])
def test_unpack_operations_accept_contiguous_byte_buffers(buffer_type):
    assert wpistruct.unpack(module.ThingA, buffer_type(b"\x07")) == module.ThingA(7)
    assert wpistruct.unpack_array(module.ThingA, buffer_type(b"\x07\x08")) == [
        module.ThingA(7),
        module.ThingA(8),
    ]


# def test_unpack_into():
#     r1 = module.ThingA(1)
#     r2 = module.ThingA(2)
#     assert r1 != r2
#     wpistruct.unpack_into(b"\x01", r2)
#     assert r1 == r2


#
# Nested struct
#


def test_nested_for_each_nested():
    l = []

    def _fn(*args):
        l.append(args)

    wpistruct.for_each_nested(module.Outer, _fn)
    assert l == [
        ("struct:ThingA", "uint8 value"),
        ("struct:Outer", "ThingA inner; int32 c"),
    ]


def test_nested_get_type_string():
    assert wpistruct.get_type_name(module.ThingA) == "ThingA"


def test_nested_get_schema():
    assert wpistruct.get_schema(module.Outer) == "ThingA inner; int32 c"


def test_nested_get_size():
    assert wpistruct.get_size(module.Outer) == 5


def test_nested_pack():
    v = module.Outer(module.ThingA(2), 4)
    assert wpistruct.pack(v) == b"\x02\x04\x00\x00\x00"


def test_nested_pack_into():
    v = module.Outer(module.ThingA(3), 5)
    buf = bytearray(5)
    wpistruct.pack_into(v, buf)
    assert buf == b"\x03\x05\x00\x00\x00"


def test_nested_unpack():
    assert wpistruct.unpack(module.ThingA, b"\x01") == module.ThingA(1)


#
# User defined serialization
#


@wpistruct.make_wpistruct(name="mystruct")
@dataclasses.dataclass
class MyStruct:
    x: int
    y: bool
    z: float


def test_user_for_each_nested():
    l = []

    def _fn(*args):
        l.append(args)

    wpistruct.for_each_nested(MyStruct, _fn)
    assert l == [("struct:mystruct", "int32 x; bool y; float z")]


def test_user_get_type_string():
    assert wpistruct.get_type_name(MyStruct) == "mystruct"


def test_user_get_schema():
    assert wpistruct.get_schema(MyStruct) == "int32 x; bool y; float z"


def test_user_get_size():
    assert wpistruct.get_size(MyStruct) == 9


def test_user_pack():
    v = MyStruct(2, True, 3.5)
    assert wpistruct.pack(v) == b"\x02\x00\x00\x00\x01\x00\x00\x60\x40"


def test_user_pack_into():
    v = MyStruct(2, True, 3.5)
    buf = bytearray(9)
    wpistruct.pack_into(v, buf)
    assert buf == b"\x02\x00\x00\x00\x01\x00\x00\x60\x40"


def test_user_unpack():
    v = MyStruct(2, True, 3.5)
    assert wpistruct.unpack(MyStruct, b"\x02\x00\x00\x00\x01\x00\x00\x60\x40") == v


_GeneratedBufferStruct = make_wpistruct_from_schema(
    "GeneratedBufferStruct", "uint16 value", nested={}
)


def _make_strided_buffer(encoded, stride):
    backing = bytearray(len(encoded) * 2)
    if stride == 2:
        buffer = memoryview(backing)[::2]
    else:
        buffer = memoryview(backing)[len(encoded) - 1 :: -1]
    buffer[:] = encoded
    return buffer


@pytest.mark.parametrize(
    ("struct_type", "scalar_bytes", "array_bytes"),
    [
        (
            module.Outer,
            b"\x01\x02\x00\x00\x00",
            b"\x01\x02\x00\x00\x00\x03\x04\x00\x00\x00",
        ),
        (
            MyStruct,
            b"\x02\x00\x00\x00\x01\x00\x00\x60\x40",
            b"\x02\x00\x00\x00\x01\x00\x00\x60\x40"
            b"\x03\x00\x00\x00\x00\x00\x00\x80\x3f",
        ),
        (_GeneratedBufferStruct, b"\x34\x12", b"\x34\x12\x78\x56"),
    ],
    ids=["native", "authored", "generated"],
)
@pytest.mark.parametrize(
    ("operation", "encoded_attribute"),
    [(wpistruct.unpack, "scalar_bytes"), (wpistruct.unpack_array, "array_bytes")],
    ids=["unpack", "unpack_array"],
)
@pytest.mark.parametrize("stride", [2, -1])
def test_unpack_operations_reject_noncontiguous_buffers(
    struct_type,
    scalar_bytes,
    array_bytes,
    operation,
    encoded_attribute,
    stride,
):
    encoded = scalar_bytes if encoded_attribute == "scalar_bytes" else array_bytes
    buffer = _make_strided_buffer(encoded, stride)
    assert bytes(buffer) == encoded

    with pytest.raises(ValueError, match="buffer must be contiguous"):
        operation(struct_type, buffer)


@wpistruct.make_wpistruct
@dataclasses.dataclass
class Empty:
    pass


def test_user_empty_struct_scalar_round_trip():
    value = Empty()

    assert wpistruct.pack(value) == b""
    assert wpistruct.unpack(Empty, b"") == value


def test_user_empty_struct_array_unpack_is_rejected():
    with pytest.raises(ValueError, match="cannot unpack an array of zero-size structs"):
        wpistruct.unpack_array(Empty, b"")


def test_pack_array_preserves_empty_and_zero_size_structs():
    assert wpistruct.pack_array([]) == b""
    assert wpistruct.pack_array([Empty(), Empty()]) == b""

    item = _PackProbe0(fail_on_call=3)
    assert wpistruct.pack_array([item, item]) == b""
    assert item.pack_calls == 2


@wpistruct.make_wpistruct(name="SingleFieldStruct")
@dataclasses.dataclass
class SingleFieldStruct:
    value: wpistruct.uint8 = 0


def test_user_single_field_unpack():
    assert wpistruct.unpack(SingleFieldStruct, b"\x01") == SingleFieldStruct(1)


@wpistruct.make_wpistruct(name="VectorStruct")
@dataclasses.dataclass
class VectorStruct:
    data: tuple[wpistruct.double, wpistruct.double, wpistruct.double]


def test_user_tuple_array_get_schema():
    assert wpistruct.get_schema(VectorStruct) == "double data[3]"


def test_user_tuple_array_get_size():
    assert wpistruct.get_size(VectorStruct) == 24


def test_user_tuple_array_pack():
    assert wpistruct.pack(VectorStruct((1.0, 2.0, 3.0))) == (
        b"\x00\x00\x00\x00\x00\x00\xf0?"
        b"\x00\x00\x00\x00\x00\x00\x00@"
        b"\x00\x00\x00\x00\x00\x00\x08@"
    )


def test_user_tuple_array_unpack():
    assert wpistruct.unpack(
        VectorStruct,
        b"\x00\x00\x00\x00\x00\x00\xf0?"
        b"\x00\x00\x00\x00\x00\x00\x00@"
        b"\x00\x00\x00\x00\x00\x00\x08@",
    ) == VectorStruct((1.0, 2.0, 3.0))


@wpistruct.make_wpistruct
@dataclasses.dataclass
class TupleArrayNameCollisionStruct:
    data: tuple[int, int]
    data_0: int


def test_user_tuple_array_unpack_does_not_collide_with_similar_field_names():
    v = TupleArrayNameCollisionStruct((1, 2), 3)

    assert wpistruct.unpack(TupleArrayNameCollisionStruct, wpistruct.pack(v)) == v


def test_user_tuple_array_rejects_mixed_types():
    with pytest.raises(
        TypeError,
        match=re.escape(
            "MixedTuple.value has unsupported tuple type hint: "
            "tuple fields must be fixed-length and homogeneous"
        ),
    ):

        @wpistruct.make_wpistruct
        @dataclasses.dataclass
        class MixedTuple:
            value: tuple[int, float]


def test_user_rejects_unsupported_type_with_tuple_in_supported_list():
    with pytest.raises(
        TypeError,
        match=re.escape(
            "BadField.value is not a wpistruct or does not have a supported type hint "
            "(supported: bool, int8, uint8, int16, uint16, int, int32, uint32, "
            "int64, uint64, float, double, or fixed-length homogeneous tuple of "
            "a supported type)"
        ),
    ):

        @wpistruct.make_wpistruct
        @dataclasses.dataclass
        class BadField:
            value: str


# def test_user_unpack_into():
#     v1 = MyStruct(2, True, 3.5)
#     v2 = MyStruct(3, True, 4.5)
#     assert v1 != v2
#     wpistruct.unpack_into(b"\x02\x00\x00\x00\x01\x00\x00\x60\x40", v2)
#     assert v1 == v2


#
# User defined serialization (nested)
#


@wpistruct.make_wpistruct
@dataclasses.dataclass
class Outer:
    x: int
    inner: MyStruct


def test_user_nested_for_each_nested():
    l = []

    def _fn(*args):
        l.append(args)

    wpistruct.for_each_nested(Outer, _fn)
    assert l == [
        ("struct:mystruct", "int32 x; bool y; float z"),
        ("struct:Outer", "int32 x; mystruct inner"),
    ]


def test_user_nested_get_type_string():
    assert wpistruct.get_type_name(Outer) == "Outer"


def test_user_nested_get_schema():
    assert wpistruct.get_schema(Outer) == "int32 x; mystruct inner"


def test_user_nested_get_size():
    assert wpistruct.get_size(Outer) == 4 + 9


def test_user_nested_pack():
    v = Outer(2, MyStruct(3, True, 4.0))
    assert wpistruct.pack(v) == b"\x02\x00\x00\x00\x03\x00\x00\x00\x01\x00\x00\x80\x40"


def test_user_nested_pack_into():
    v = Outer(2, MyStruct(3, True, 4.0))
    buf = bytearray(4 + 9)
    wpistruct.pack_into(v, buf)
    assert buf == b"\x02\x00\x00\x00\x03\x00\x00\x00\x01\x00\x00\x80\x40"


def test_user_nested_unpack():
    assert wpistruct.unpack(
        Outer, b"\x02\x00\x00\x00\x03\x00\x00\x00\x01\x00\x00\x80\x40"
    ) == Outer(2, MyStruct(3, True, 4.0))
