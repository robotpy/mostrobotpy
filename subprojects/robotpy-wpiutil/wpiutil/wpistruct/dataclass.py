import dataclasses
import typing

#
# Use these types to specify explicitly sized integers, but you can
# also use int/bool/float
#

# fmt: off

if typing.TYPE_CHECKING:
    int8 = int
    uint8 = int
    int16 = int
    uint16 = int
    int32 = int
    uint32 = int
    int64 = int
    uint64 = int
    double = float
else:
    class int8(int): pass
    class uint8(int): pass
    class int16(int): pass
    class uint16(int): pass
    class int32(int): pass
    class uint32(int): pass
    class int64(int): pass
    class uint64(int): pass

    class double(float): pass

# fmt: on


class char(str):
    """A scalar character occupying exactly one UTF-8 byte, including ``'\\0'``.

    Use this as a field annotation. Packed values may be plain strings, but
    empty strings and multibyte characters are rejected.
    """

    def __new__(cls, value: str, /):
        if not isinstance(value, str):
            raise TypeError("char value must be str")
        if len(value.encode("utf-8")) != 1:
            raise ValueError("char value must occupy exactly one UTF-8 byte")
        return super().__new__(cls, value)


@dataclasses.dataclass(frozen=True, slots=True)
class CharArray:
    """Fixed UTF-8 byte capacity for ``Annotated[str, CharArray(size)]``.

    ``size`` must be a positive integer. Short strings are zero-padded; strings
    whose UTF-8 encoding exceeds the capacity are rejected, not truncated.
    Unpacking removes trailing zero padding, so trailing NUL characters are
    not preserved.
    """

    size: int

    def __post_init__(self):
        if (
            isinstance(self.size, bool)
            or not isinstance(self.size, int)
            or self.size <= 0
        ):
            raise ValueError("CharArray size must be a positive integer")


@dataclasses.dataclass(frozen=True, slots=True)
class BitField:
    """Bit width for an ``Annotated`` scalar boolean, sized integer, or enum.

    ``width`` must be positive and cannot exceed the integer storage width.
    Boolean fields require width 1. Enum fields also require a sized integer
    storage annotation. Arrays cannot be bitfields.
    """

    width: int

    def __post_init__(self):
        if (
            isinstance(self.width, bool)
            or not isinstance(self.width, int)
            or self.width <= 0
        ):
            raise ValueError("BitField width must be a positive integer")


def make_wpistruct(cls=None, /, *, name: str | None = None):
    """
    This decorator allows you to easily define a custom type that can be
    used with wpilib's custom serialization protocol (for use in datalog
    and networktables). Just create a normal python dataclass, and apply
    this decorator to the class.

    For example, here's how you define a dataclass that contains an integer,
    a boolean, and a double::

        @wpiutil.wpistruct.make_wpistruct(name="mystruct")
        @dataclasses.dataclass
        class MyStruct:
            x: wpiutil.wpistruct.int32
            y: bool
            z: wpiutil.wpistruct.double

    The types defined in the dataclass can be another WPIStruct compatible class
    (either builtin or user defined); one of int, bool, or float; a fixed-length
    homogeneous tuple of those supported types; or you can use one of the
    ``wpiutil.wpistruct.[u]int*`` values for explicitly sized integer types.

    Use :class:`typing.Annotated` to specify enum storage, bitfields, or fixed
    character arrays::

        import dataclasses
        import enum
        from typing import Annotated
        from wpiutil import wpistruct

        class Mode(enum.IntEnum):
            OFF = 0
            ON = 1

        @wpistruct.make_wpistruct
        @dataclasses.dataclass
        class Packet:
            mode: Annotated[Mode, wpistruct.uint8, wpistruct.BitField(2)]
            enabled: Annotated[bool, wpistruct.BitField(1)]
            label: Annotated[str, wpistruct.CharArray(8)]
            initial: wpistruct.char
            modes: Annotated[tuple[Mode, Mode], wpistruct.uint8]

    Enum fields require an :class:`enum.IntEnum` and an explicit sized integer
    storage type. For enum arrays, apply the storage metadata to the tuple,
    not its elements. Enum declarations must fit the storage range (or the
    bitfield range, when specified), and packed values must be instances of
    the annotated enum, not plain integers.

    Unrecognized enum values unpack as instances of the enum with names such
    as ``UNKNOWN_7``, without modifying its declared members or invoking its
    ``_missing_`` hook. A bounded per-field cache reuses recent unknown values;
    object identity is not guaranteed after eviction. Compare values using
    equality, not ``is``.

    Bitfields support booleans (width 1), explicitly sized integers, and
    enums with explicitly sized storage. Arrays and plain ``int`` annotations
    cannot be bitfields. Values must fit the declared signed or unsigned range.

    ``char`` requires exactly one UTF-8 byte. ``CharArray`` specifies a positive
    byte capacity, not a character count: shorter strings are zero-padded and
    oversized UTF-8 encodings are rejected. Unpacking strips trailing zero
    padding, so trailing NUL characters are not preserved.
    """

    def wrap(cls):
        from ._compiler import compile_wpistruct

        return compile_wpistruct(cls, name)

    if cls is None:
        return wrap

    return wrap(cls)
