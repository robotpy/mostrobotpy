import dataclasses


@dataclasses.dataclass(frozen=True, slots=True)
class StructFieldLayout:
    schema_name: str
    python_name: str
    type_name: str
    offset: int
    size: int
    array_size: int
    bit_width: int
    bit_shift: int
    bit_mask: int
    enum_values: tuple[tuple[str, int], ...]
    nested_type: type | None


@dataclasses.dataclass(frozen=True, slots=True)
class StructLayout:
    type_name: str
    schema: str
    size: int
    fields: tuple[StructFieldLayout, ...]
