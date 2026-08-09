import dataclasses
import enum
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


def test_legacy_tuple_element_annotated_metadata_uses_base_type():
    @wpistruct.make_wpistruct
    @dataclasses.dataclass
    class AnnotatedTuple:
        value: tuple[Annotated[wpistruct.uint8, "application metadata"]]

    value = AnnotatedTuple((7,))
    assert wpistruct.get_schema(AnnotatedTuple) == "uint8 value[1]"
    assert wpistruct.unpack(AnnotatedTuple, wpistruct.pack(value)) == value


def test_legacy_metadata_equality_is_not_evaluated():
    class ApplicationMetadata:
        def __eq__(self, other):
            raise AssertionError("application metadata equality was evaluated")

    @wpistruct.make_wpistruct
    @dataclasses.dataclass
    class AnnotatedValue:
        value: Annotated[int, ApplicationMetadata()]

    value = AnnotatedValue(7)
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


def test_legacy_unicode_field_names_preserve_schema_bytes_and_layout():
    unicode_struct = dataclasses.make_dataclass(
        "LegacyUnicode",
        [
            ("é", wpistruct.int32),
            ("π", wpistruct.uint16),
            ("变量", bool),
            ("aé", wpistruct.int8),
        ],
    )
    unicode_struct = wpistruct.make_wpistruct(name="LegacyUnicode")(unicode_struct)
    value = unicode_struct(-2, 0x1234, True, -3)
    encoded = b"\xfe\xff\xff\xff\x34\x12\x01\xfd"

    assert wpistruct.get_schema(unicode_struct) == (
        "int32 é; uint16 π; bool 变量; int8 aé"
    )
    assert wpistruct.pack(value) == encoded
    assert wpistruct.unpack(unicode_struct, encoded) == value
    assert unicode_struct.__wpistruct_descriptor__.schema == (
        "int32 é; uint16 π; bool 变量; int8 aé"
    )
    assert [
        (field.schema_name, field.python_name)
        for field in unicode_struct.__wpistruct_descriptor__.fields
    ] == [("é", "é"), ("π", "π"), ("变量", "变量"), ("aé", "aé")]


def test_nested_legacy_unicode_fields_preserve_public_behavior():
    inner = dataclasses.make_dataclass("UnicodeInner", [("变量", wpistruct.uint16)])
    inner = wpistruct.make_wpistruct(name="UnicodeInner")(inner)
    outer = dataclasses.make_dataclass(
        "UnicodeOuter", [("π", inner), ("aé", wpistruct.int8)]
    )
    outer = wpistruct.make_wpistruct(name="UnicodeOuter")(outer)
    value = outer(inner(0x1234), -2)
    encoded = b"\x34\x12\xfe"

    assert wpistruct.get_schema(inner) == "uint16 变量"
    assert wpistruct.get_schema(outer) == "UnicodeInner π; int8 aé"
    assert wpistruct.pack(value) == encoded
    assert wpistruct.unpack(outer, encoded) == value
    assert outer.__wpistruct_descriptor__.schema == "UnicodeInner π; int8 aé"
    assert [
        (field.schema_name, field.python_name)
        for field in outer.__wpistruct_descriptor__.fields
    ] == [("π", "π"), ("aé", "aé")]

    nested_schemas = []
    wpistruct.for_each_nested(
        outer,
        lambda type_name, schema: nested_schemas.append((type_name, schema)),
    )
    assert nested_schemas == [
        ("struct:UnicodeInner", "uint16 变量"),
        ("struct:UnicodeOuter", "UnicodeInner π; int8 aé"),
    ]


class Mode(enum.IntEnum):
    OFF = 0
    AUTO = 1
    DEFAULT = 1


_hostile_missing_calls = []


class HostileMissingMode(enum.IntEnum):
    OFF = 0
    AUTO = 1

    @classmethod
    def _missing_(cls, value):
        _hostile_missing_calls.append(value)
        cls._member_map_["INJECTED"] = cls.AUTO
        return cls.AUTO


@wpistruct.make_wpistruct(name="Packet")
@dataclasses.dataclass
class Packet:
    initial: wpistruct.char
    name: Annotated[str, wpistruct.CharArray(5)]
    mode: Annotated[Mode, wpistruct.uint8]


def test_char_and_enum_schema_round_trip():
    value = Packet(wpistruct.char("A"), "ab\0c", Mode.AUTO)
    assert wpistruct.get_schema(Packet) == (
        "char initial; char name[5]; " "enum {OFF=0,AUTO=1,DEFAULT=1} uint8 mode"
    )
    assert wpistruct.pack(value) == b"Aab\0c\0\x01"
    assert wpistruct.unpack(Packet, wpistruct.pack(value)) == value


def test_unknown_enum_value_is_typed_without_mutating_enum():
    before_members = dict(Mode.__members__)
    before_values = dict(Mode._value2member_map_)
    value = wpistruct.unpack(Packet, b"Aab\0c\0\x07")
    assert isinstance(value.mode, Mode)
    assert value.mode.name == "UNKNOWN_7"
    assert value.mode.value == 7
    assert Mode.__members__ == before_members
    assert Mode._value2member_map_ == before_values
    assert list(Mode) == [Mode.OFF, Mode.AUTO]


@wpistruct.make_wpistruct
@dataclasses.dataclass
class EnumCache:
    first: Annotated[Mode, wpistruct.uint8]
    second: Annotated[Mode, wpistruct.uint8]


def test_unknown_enum_pseudo_members_are_cached_per_field():
    first = wpistruct.unpack(EnumCache, b"\x07\x07")
    second = wpistruct.unpack(EnumCache, b"\x07\x07")

    assert first.first is second.first
    assert first.second is second.second
    assert first.first is not first.second


@wpistruct.make_wpistruct
@dataclasses.dataclass
class HostileMissingPacket:
    mode: Annotated[HostileMissingMode, wpistruct.uint8]


def test_enum_unpack_does_not_call_missing_or_mutate_class_maps():
    _hostile_missing_calls.clear()
    before_members = dict(HostileMissingMode.__members__)
    before_values = dict(HostileMissingMode._value2member_map_)

    known = wpistruct.unpack(HostileMissingPacket, b"\x01")
    first_unknown = wpistruct.unpack(HostileMissingPacket, b"\x07")
    second_unknown = wpistruct.unpack(HostileMissingPacket, b"\x07")

    assert known.mode is HostileMissingMode.AUTO
    assert first_unknown.mode is second_unknown.mode
    assert first_unknown.mode.name == "UNKNOWN_7"
    assert first_unknown.mode.value == 7
    assert _hostile_missing_calls == []
    assert HostileMissingMode.__members__ == before_members
    assert HostileMissingMode._value2member_map_ == before_values


@wpistruct.make_wpistruct
@dataclasses.dataclass
class AuthoredSingletonArrays:
    initial: wpistruct.char
    samples: tuple[wpistruct.uint8]
    modes: Annotated[tuple[Mode], wpistruct.uint8]
    nested: tuple[Legacy]


def test_descriptor_codec_preserves_authored_singleton_tuple_semantics():
    value = AuthoredSingletonArrays(
        wpistruct.char("A"), (7,), (Mode.AUTO,), (Legacy(2, (3, 4)),)
    )

    assert wpistruct.get_schema(AuthoredSingletonArrays) == (
        "char initial; uint8 samples[1]; "
        "enum {OFF=0,AUTO=1,DEFAULT=1} uint8 modes[1]; Legacy nested[1]"
    )
    assert wpistruct.pack(value) == b"A\x07\x01\x02\0\0\0\x03\0\x04\0"
    assert wpistruct.unpack(AuthoredSingletonArrays, wpistruct.pack(value)) == value


@wpistruct.make_wpistruct
@dataclasses.dataclass
class AuthoredDescriptorArrays:
    samples: tuple[wpistruct.uint16, wpistruct.uint16]
    modes: Annotated[tuple[Mode, Mode], wpistruct.uint8]
    nested: tuple[Legacy, Legacy]


def test_descriptor_codec_authored_arrays_larger_than_one_have_literal_layout():
    value = AuthoredDescriptorArrays(
        (0x1234, 0xABCD),
        (Mode.OFF, Mode.AUTO),
        (Legacy(1, (2, 3)), Legacy(-1, (4, 5))),
    )
    encoded = (
        b"\x34\x12\xcd\xab\x00\x01"
        b"\x01\x00\x00\x00\x02\x00\x03\x00"
        b"\xff\xff\xff\xff\x04\x00\x05\x00"
    )

    assert wpistruct.get_schema(AuthoredDescriptorArrays) == (
        "uint16 samples[2]; "
        "enum {OFF=0,AUTO=1,DEFAULT=1} uint8 modes[2]; Legacy nested[2]"
    )
    assert wpistruct.pack(value) == encoded
    assert wpistruct.unpack(AuthoredDescriptorArrays, encoded) == value


@wpistruct.make_wpistruct
@dataclasses.dataclass
class SharedBits:
    a: Annotated[wpistruct.int16, wpistruct.BitField(2)]
    b: Annotated[bool, wpistruct.BitField(1)]
    c: Annotated[bool, wpistruct.BitField(1)]
    d: Annotated[wpistruct.uint16, wpistruct.BitField(5)]


def test_shared_bitfield_round_trip():
    value = SharedBits(-1, True, False, 17)
    assert wpistruct.get_schema(SharedBits) == (
        "int16 a:2; bool b:1; bool c:1; uint16 d:5"
    )
    assert wpistruct.get_size(SharedBits) == 2
    assert wpistruct.pack(value) == b"\x17\x01"
    assert wpistruct.unpack(SharedBits, b"\x17\x01") == value


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
    ("struct_type", "value", "size", "schema", "encoded"),
    [
        (
            DifferentWidthBits,
            DifferentWidthBits(-1, -2),
            6,
            "int32 a:2; int16 b:2",
            b"\x03\x00\x00\x00\x02\x00",
        ),
        (
            OverflowBits,
            OverflowBits(-1, -2),
            2,
            "int8 a:4; int8 b:5",
            b"\x0f\x1e",
        ),
        (
            BoolFirst8,
            BoolFirst8(True, -2),
            1,
            "bool a:1; int8 b:5",
            b"\x3d",
        ),
        (
            BoolFirst16,
            BoolFirst16(True, -2),
            3,
            "bool a:1; int16 b:5",
            b"\x01\x1e\x00",
        ),
        (
            BoolAfterFullUnit,
            BoolAfterFullUnit(-1, True),
            3,
            "int16 a:16; bool b:1",
            b"\xff\xff\x01",
        ),
    ],
)
def test_authored_bitfield_storage_transitions(
    struct_type, value, size, schema, encoded
):
    assert wpistruct.get_schema(struct_type) == schema
    assert wpistruct.get_size(struct_type) == size
    assert wpistruct.pack(value) == encoded
    assert wpistruct.unpack(struct_type, encoded) == value


class SignedMode(enum.IntEnum):
    REVERSE = -1
    FORWARD = 1


@wpistruct.make_wpistruct
@dataclasses.dataclass
class MetadataOrder:
    mode: Annotated[
        SignedMode,
        wpistruct.BitField(2),
        "application metadata",
        wpistruct.int8,
    ]


def test_complete_annotated_metadata_is_accepted_in_any_order():
    value = MetadataOrder(SignedMode.REVERSE)
    assert wpistruct.get_schema(MetadataOrder) == (
        "enum {REVERSE=-1,FORWARD=1} int8 mode:2"
    )
    assert wpistruct.pack(value) == b"\x03"
    assert wpistruct.unpack(MetadataOrder, b"\x03") == value


class Huge(enum.IntEnum):
    VALUE = 256


class TooWideForSignedBitfield(enum.IntEnum):
    VALUE = 2


@pytest.mark.parametrize(
    ("annotation", "match"),
    [
        (Annotated[float, wpistruct.BitField(1)], "cannot be bitfield"),
        (Annotated[wpistruct.char, wpistruct.BitField(1)], "cannot be bitfield"),
        (Annotated[Legacy, wpistruct.BitField(1)], "cannot be bitfield"),
        (Annotated[bool, wpistruct.BitField(2)], "width must be 1"),
        (
            Annotated[wpistruct.int16, wpistruct.BitField(17)],
            "exceeds type size",
        ),
        (Mode, "requires sized integer storage"),
        (
            Annotated[Mode, wpistruct.uint8, wpistruct.int16],
            "multiple storage",
        ),
        (
            Annotated[tuple[wpistruct.int8, wpistruct.int8], wpistruct.BitField(2)],
            "array.*bitfield",
        ),
        (Annotated[Huge, wpistruct.uint8], "VALUE.*does not fit"),
        (
            Annotated[
                TooWideForSignedBitfield,
                wpistruct.int8,
                wpistruct.BitField(2),
            ],
            "VALUE.*does not fit",
        ),
        (
            Annotated[str, wpistruct.CharArray(2), wpistruct.CharArray(3)],
            "multiple CharArray",
        ),
        (
            Annotated[wpistruct.int8, wpistruct.CharArray(2)],
            "CharArray.*only.*str",
        ),
        (
            Annotated[wpistruct.int8, wpistruct.BitField(1), wpistruct.BitField(1)],
            "multiple bitfield",
        ),
    ],
)
def test_invalid_complete_grammar_annotations(annotation, match):
    cls = dataclasses.make_dataclass("InvalidField", [("value", annotation)])
    with pytest.raises(TypeError, match=match):
        wpistruct.make_wpistruct(cls)


@pytest.mark.parametrize(
    ("text", "size", "encoded"),
    [
        ("a\u0234", 3, b"a\xc8\xb4"),
        ("a\u1234", 4, b"a\xe1\x88\xb4"),
        ("a\U0001f400", 5, b"a\xf0\x9f\x90\x80"),
    ],
)
def test_authored_char_array_utf8_boundaries_fit(text, size, encoded):
    cls = dataclasses.make_dataclass(
        f"Text{size}", [("text", Annotated[str, wpistruct.CharArray(size)])]
    )
    wpistruct.make_wpistruct(cls)

    assert wpistruct.pack(cls(text)) == encoded
    assert wpistruct.unpack(cls, encoded) == cls(text)


@pytest.mark.parametrize(
    ("text", "size", "unchanged"),
    [
        ("a\u0234", 2, b"\xa5\xa5"),
        ("a\u1234", 2, b"\xa5\xa5"),
        ("a\u1234", 3, b"\xa5\xa5\xa5"),
        ("a\U0001f400", 2, b"\xa5\xa5"),
        ("a\U0001f400", 3, b"\xa5\xa5\xa5"),
        ("a\U0001f400", 4, b"\xa5\xa5\xa5\xa5"),
    ],
)
def test_authored_char_array_rejects_partial_utf8_atomically(text, size, unchanged):
    cls = dataclasses.make_dataclass(
        f"Text{size}", [("text", Annotated[str, wpistruct.CharArray(size)])]
    )
    wpistruct.make_wpistruct(cls)
    destination = bytearray(unchanged)

    with pytest.raises(ValueError, match=rf"Text{size}: error packing data") as exc:
        cls.WPIStruct.pack_into(cls(text), destination)

    assert str(exc.value.__cause__).endswith(f"must fit in {size} bytes")
    assert destination == unchanged


@pytest.mark.parametrize(
    ("number_type", "minimum", "maximum", "below", "above"),
    [
        (wpistruct.int8, -(2**7), 2**7 - 1, -(2**7) - 1, 2**7),
        (wpistruct.int16, -(2**15), 2**15 - 1, -(2**15) - 1, 2**15),
        (wpistruct.int32, -(2**31), 2**31 - 1, -(2**31) - 1, 2**31),
        (wpistruct.int64, -(2**63), 2**63 - 1, -(2**63) - 1, 2**63),
        (wpistruct.uint8, 0, 2**8 - 1, -1, 2**8),
        (wpistruct.uint16, 0, 2**16 - 1, -1, 2**16),
        (wpistruct.uint32, 0, 2**32 - 1, -1, 2**32),
        (wpistruct.uint64, 0, 2**64 - 1, -1, 2**64),
    ],
)
def test_descriptor_codec_enforces_authored_integer_boundaries(
    number_type, minimum, maximum, below, above
):
    cls = dataclasses.make_dataclass(
        f"Boundary{number_type.__name__}",
        [("value", number_type), ("initial", wpistruct.char)],
    )
    wpistruct.make_wpistruct(cls)

    for number in (minimum, maximum):
        value = cls(number, wpistruct.char("A"))
        assert wpistruct.unpack(cls, wpistruct.pack(value)) == value

    for number in (below, above):
        with pytest.raises(ValueError, match="error packing data") as exc:
            wpistruct.pack(cls(number, wpistruct.char("A")))
        assert "field value must be between" in str(exc.value.__cause__)


@wpistruct.make_wpistruct
@dataclasses.dataclass
class SignedNibble:
    value: Annotated[wpistruct.int8, wpistruct.BitField(4)]


def test_authored_signed_bitfield_boundaries():
    for number in (-8, 7):
        value = SignedNibble(number)
        assert wpistruct.unpack(SignedNibble, wpistruct.pack(value)) == value

    for number in (-9, 8):
        with pytest.raises(ValueError, match="error packing data") as exc:
            wpistruct.pack(SignedNibble(number))
        assert "field value must be between -8 and 7" in str(exc.value.__cause__)


def test_descriptor_pack_into_callback_succeeds_atomically():
    value = Packet(wpistruct.char("A"), "ab\0c", Mode.AUTO)
    destination = bytearray(b"\xa5" * wpistruct.get_size(Packet))

    Packet.WPIStruct.pack_into(value, destination)

    assert destination == b"Aab\0c\0\x01"


def test_descriptor_codec_requires_enum_instances_and_pack_into_is_atomic():
    destination = bytearray(b"\xa5" * wpistruct.get_size(Packet))

    with pytest.raises(
        ValueError,
        match=r"Packet \(test_struct_annotations\.Packet\): error packing data",
    ) as exc:
        Packet.WPIStruct.pack_into(
            Packet(wpistruct.char("A"), "ok", 1),
            destination,
        )

    assert "must be a Mode instance" in str(exc.value.__cause__)
    assert destination == b"\xa5" * 7


def test_descriptor_codec_preserves_unpack_error_wrapper():
    with pytest.raises(
        ValueError,
        match=r"Packet \(test_struct_annotations\.Packet\): error unpacking data",
    ) as exc:
        Packet.WPIStruct.unpack(b"\0")

    assert "buffer must be 7 bytes" in str(exc.value.__cause__)
