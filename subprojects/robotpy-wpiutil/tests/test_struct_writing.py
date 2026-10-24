import dataclasses
import enum
from typing import Annotated

from wpiutil import wpistruct


def test_authored_writing_features_without_layout_metadata():
    class Mode(enum.IntEnum):
        OFF = 0
        ON = 1

    @wpistruct.make_wpistruct
    @dataclasses.dataclass
    class Packet:
        mode: Annotated[Mode, wpistruct.uint8, wpistruct.BitField(2)]
        enabled: Annotated[bool, wpistruct.BitField(1)]
        label: Annotated[str, wpistruct.CharArray(4)]
        initial: wpistruct.char

    value = Packet(Mode.ON, True, "ok", "x")
    encoded = b"\x05ok\0\0x"
    assert wpistruct.pack(value) == encoded
    assert wpistruct.unpack(Packet, encoded) == value
    buffer = bytearray(len(encoded))
    wpistruct.pack_into(value, buffer)
    assert buffer == encoded
    assert not hasattr(Packet, "__wpistruct_descriptor__")
    assert not hasattr(wpistruct, "StructLayout")
    assert not hasattr(wpistruct, "StructFieldLayout")
