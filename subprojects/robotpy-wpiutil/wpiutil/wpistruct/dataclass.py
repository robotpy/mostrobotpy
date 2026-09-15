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
        if (
            isinstance(self.size, bool)
            or not isinstance(self.size, int)
            or self.size <= 0
        ):
            raise ValueError("CharArray size must be a positive integer")


@dataclasses.dataclass(frozen=True, slots=True)
class BitField:
    width: int

    def __post_init__(self):
        if (
            isinstance(self.width, bool)
            or not isinstance(self.width, int)
            or self.width <= 0
        ):
            raise ValueError("BitField width must be a positive integer")


def make_wpistruct(cls=None, /, *, name: typing.Optional[str] = None):
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
            z: wpiutil.struct.double

    The types defined in the dataclass can be another WPIStruct compatible class
    (either builtin or user defined); one of int, bool, or float; a fixed-length
    homogeneous tuple of those supported types; or you can use one of the
    ``wpiutil.wpistruct.[u]int*`` values for explicitly sized integer types.
    """

    def wrap(cls):
        from ._compiler import compile_wpistruct

        return compile_wpistruct(cls, name)

    if cls is None:
        return wrap

    return wrap(cls)
