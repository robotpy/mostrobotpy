import dataclasses

from wpiutil import wpistruct


@wpistruct.make_wpistruct(name="ExampleRecord")
@dataclasses.dataclass
class ExampleRecord:
    i: wpistruct.int32 = 0
    j: wpistruct.int32 = 0
