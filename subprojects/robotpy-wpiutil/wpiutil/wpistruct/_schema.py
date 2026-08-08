import dataclasses
import enum
import keyword
import re
import typing

from .._wpiutil import wpistruct
from .._wpiutil._schema import SchemaDatabase
from ._compiler import compile_wpistruct
from .dataclass import (
    BitField,
    CharArray,
    char,
    double,
    int8,
    int16,
    int32,
    int64,
    uint8,
    uint16,
    uint32,
    uint64,
)


class InvalidStructSchema(ValueError):
    pass


_SPECIAL_ATTRIBUTE_NAMES = {
    "__class__",
    "__dict__",
    "__weakref__",
    "__dataclass_fields__",
    "__dataclass_params__",
    "__match_args__",
}

_GENERATED_ATTRIBUTE_NAMES = {
    "WPIStruct",
    "__wpistruct_descriptor__",
}

_PRIMITIVE_TYPES = {
    "bool": bool,
    "char": char,
    "int8": int8,
    "int16": int16,
    "int32": int32,
    "int64": int64,
    "uint8": uint8,
    "uint16": uint16,
    "uint32": uint32,
    "uint64": uint64,
    "float": float,
    "double": double,
}


def _sanitize_identifier(value: str) -> str:
    value = re.sub(r"\W", "_", value)
    if not value:
        value = "_"
    if value[0].isdigit():
        value = f"_{value}"
    if not value.isidentifier():
        identifier = ""
        for character in value:
            candidate = f"{identifier}{character}"
            identifier += character if candidate.isidentifier() else "_"
        value = identifier
    if (
        keyword.iskeyword(value)
        or value in _SPECIAL_ATTRIBUTE_NAMES
        or hasattr(object, value)
    ):
        value = f"{value}_"
    return value


def _unique_identifier(value: str, used: set[str]) -> str:
    identifier = _sanitize_identifier(value)
    if identifier not in used:
        used.add(identifier)
        return identifier

    suffix = 2
    separator = "" if identifier.endswith("_") else "_"
    while f"{identifier}{separator}{suffix}" in used:
        suffix += 1
    identifier = f"{identifier}{separator}{suffix}"
    used.add(identifier)
    return identifier


def _upper_first(value: str) -> str:
    return f"{value[:1].upper()}{value[1:]}"


def _field_declaration_shape(schema: str, field_name: str) -> tuple[bool, bool]:
    pattern = re.compile(
        rf"(?<!\w){re.escape(field_name)}\s*"
        r"(?P<array>\[\s*\d+\s*\])?\s*"
        r"(?P<bitfield>:\s*\d+)?\s*(?:;|$)"
    )
    matches = tuple(pattern.finditer(schema))
    if not matches:
        return False, False
    match = matches[-1]
    return match.group("array") is not None, match.group("bitfield") is not None


def _field_is_enum(schema: str, field_name: str) -> bool:
    return (
        re.search(
            r"(?:enum\s*)?\{[^}]*\}\s*\w+\s+"
            rf"{re.escape(field_name)}\s*"
            r"(?:\[\s*\d+\s*\])?\s*(?::\s*\d+)?\s*(?:;|$)",
            schema,
        )
        is not None
    )


def _fixed_tuple(element_type: type, size: int):
    return tuple[tuple(element_type for _ in range(size))]


def _is_enum_reserved_name(value: str) -> bool:
    is_sunder = (
        len(value) > 2
        and value[0] == value[-1] == "_"
        and value[1] != "_"
        and value[-2] != "_"
    )
    is_dunder = len(value) > 4 and value.startswith("__") and value.endswith("__")
    return is_sunder or is_dunder


def _make_enum_type(
    struct_name: str, field_name: str, enum_values, used_class_names: set[str]
):
    class_name = _sanitize_identifier(struct_name.rsplit("::", 1)[-1])
    field_part = _upper_first(_sanitize_identifier(field_name))
    enum_name = _unique_identifier(f"{class_name}{field_part}", used_class_names)
    used_names: set[str] = set()
    members = []
    for member_name, value in enum_values:
        member_name = _sanitize_identifier(member_name)
        if member_name == "mro":
            member_name = "mro_"
        elif _is_enum_reserved_name(member_name):
            member_name = f"{member_name}member"
        member_name = _unique_identifier(member_name, used_names)
        members.append((member_name, value))
    return enum.IntEnum(enum_name, members, module=__name__)


def _field_annotation(
    struct_name: str,
    schema: str,
    field,
    python_name: str,
    nested,
    used_enum_names: set[str],
):
    is_array, is_bitfield = _field_declaration_shape(schema, field.name)
    is_array = is_array or field.array_size != 1

    if field.struct_name is not None:
        try:
            annotation = nested[field.struct_name]
        except KeyError:
            raise ValueError(
                f"nested struct type {field.struct_name} is not registered"
            ) from None
        metadata = []
    elif field.enum_values or _field_is_enum(schema, field.name):
        annotation = _make_enum_type(
            struct_name, python_name, field.enum_values, used_enum_names
        )
        metadata = [_PRIMITIVE_TYPES[field.type]]
    else:
        annotation = _PRIMITIVE_TYPES[field.type]
        metadata = []

    if annotation is char and is_array:
        return typing.Annotated[str, CharArray(field.array_size)]

    if is_array:
        annotation = _fixed_tuple(annotation, field.array_size)
    if is_bitfield:
        metadata.append(BitField(field.bit_width))
    if metadata:
        annotation = typing.Annotated[annotation, *metadata]
    return annotation


def _add_schema(database: SchemaDatabase, type_name: str, schema: str):
    try:
        return database.add(type_name, schema)
    except UnicodeDecodeError as exc:
        raise InvalidStructSchema(f"parse error: {exc}") from exc
    except ValueError as exc:
        if str(exc).startswith("parse error:"):
            raise InvalidStructSchema(str(exc)) from exc
        raise


def _seed_nested_database(database: SchemaDatabase, nested) -> None:
    def add_nested(type_string: str, schema: str):
        database.add(type_string.removeprefix("struct:"), schema)

    for nested_type in nested.values():
        wpistruct.for_each_nested(nested_type, add_nested)


def make_wpistruct_from_schema(
    name: str,
    schema: str,
    *,
    nested: typing.Mapping[str, type],
    descriptor=None,
) -> type:
    if descriptor is None:
        database = SchemaDatabase()
        _seed_nested_database(database, nested)
        descriptor = _add_schema(database, name, schema)

    if not descriptor.is_valid:
        missing = next(
            (
                field.struct_name
                for field in descriptor.fields
                if field.struct_name is not None and field.struct_name not in nested
            ),
            None,
        )
        if missing is not None:
            raise ValueError(f"nested struct type {missing} is not registered")
        raise ValueError(f"descriptor {name} is not valid")

    class_name = _sanitize_identifier(name.rsplit("::", 1)[-1])
    used_names: set[str] = set()
    fields = []
    python_names = []
    used_enum_names: set[str] = set()
    for field in descriptor.fields:
        field_name = field.name
        if field_name in _GENERATED_ATTRIBUTE_NAMES:
            field_name = f"{field_name}_"
        python_name = _unique_identifier(field_name, used_names)
        annotation = _field_annotation(
            name, schema, field, python_name, nested, used_enum_names
        )
        fields.append((python_name, annotation))
        python_names.append(python_name)

    generated = dataclasses.make_dataclass(
        class_name,
        fields,
        module=__name__,
    )
    generated = compile_wpistruct(
        generated,
        name,
        schema_override=schema,
        descriptor=descriptor,
        python_names=python_names,
    )
    for field in dataclasses.fields(generated):
        annotation = field.type
        if typing.get_origin(annotation) is typing.Annotated:
            field.type = typing.get_args(annotation)[0]
    return generated


class StructTypeRegistry:
    def __init__(self, struct_types: typing.Iterable[type]):
        self._database = SchemaDatabase()
        self._types: dict[str, type] = {}
        self._descriptors = {}
        self._supplied_names: set[str] = set()

        supplied_types = tuple(struct_types)
        for struct_type in supplied_types:
            type_name = wpistruct.get_type_name(struct_type)
            existing = self._types.get(type_name)
            if existing is not None and existing is not struct_type:
                raise ValueError(f"duplicate supplied struct type {type_name}")
            self._types[type_name] = struct_type
            self._supplied_names.add(type_name)

        def add_nested(type_string: str, schema: str):
            type_name = type_string.removeprefix("struct:")
            self._descriptors[type_name] = self._database.add(type_name, schema)

        for struct_type in supplied_types:
            wpistruct.for_each_nested(struct_type, add_nested)

    def get(self, type_name: str) -> type | None:
        return self._types.get(type_name)

    def add_schema(self, type_name: str, schema: str) -> type:
        if type_name in self._supplied_names:
            return self._types[type_name]

        descriptor = _add_schema(self._database, type_name, schema)

        existing = self._types.get(type_name)
        if existing is not None:
            return existing

        generated = make_wpistruct_from_schema(
            type_name,
            schema,
            nested=self._types,
            descriptor=descriptor,
        )
        self._types[type_name] = generated
        self._descriptors[type_name] = descriptor
        return generated
