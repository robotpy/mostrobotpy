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


class _UnresolvedStructSchema(ValueError):
    def __init__(self, type_name: str):
        self.type_name = type_name
        super().__init__(f"nested struct type {type_name} is not registered")


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

# Generated fixed arrays are represented as Python tuples and as fixed tuple
# annotations containing one type reference per element. A cumulative 65,536
# elements caps each class's annotation pointer payload at 512 KiB on 64-bit
# CPython while leaving ample room for ordinary robotics sample arrays. Larger
# schemas remain valid WPILib grammar, but are not safely representable as
# generated Python classes.
_MAX_GENERATED_TUPLE_ELEMENTS = 65_536


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
    field,
    python_name: str,
    nested,
    used_enum_names: set[str],
):
    is_array = field.is_array

    if field.struct_name is not None:
        try:
            annotation = nested[field.struct_name]
        except KeyError:
            raise _UnresolvedStructSchema(field.struct_name) from None
        metadata = []
    elif field.is_enum:
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
    if field.is_bit_field:
        metadata.append(BitField(field.bit_width))
    if metadata:
        annotation = typing.Annotated[annotation, *metadata]
    return annotation


def _schema_operation(operation, type_name: str, schema: str):
    try:
        return operation(type_name, schema)
    except UnicodeDecodeError as exc:
        raise InvalidStructSchema(f"parse error: {exc}") from exc
    except ValueError as exc:
        if str(exc).startswith("parse error:"):
            raise InvalidStructSchema(str(exc)) from exc
        raise


def _add_schema(database: SchemaDatabase, type_name: str, schema: str):
    return _schema_operation(database.add, type_name, schema)


def _stage_schema(database: SchemaDatabase, type_name: str, schema: str):
    return _schema_operation(database.stage, type_name, schema)


def _native_seed_schema(struct_type: type) -> str:
    layout = struct_type.__wpistruct_descriptor__
    declarations = []
    for index, field in enumerate(layout.fields):
        if field.enum_values:
            values = ",".join(f"{name}={value}" for name, value in field.enum_values)
            type_name = f"enum {{{values}}} {field.type_name}"
        else:
            type_name = field.type_name
        array_suffix = f"[{field.array_size}]" if field.array_size > 1 else ""
        is_bitfield = field.nested_type is None and (
            field.bit_shift != 0 or field.bit_width != field.size * 8
        )
        bitfield_suffix = f":{field.bit_width}" if is_bitfield else ""
        declarations.append(f"{type_name} field{index}{array_suffix}{bitfield_suffix}")
    return "; ".join(declarations)


def _add_nested_dependency_schemas(
    database: SchemaDatabase,
    descriptor,
    nested: typing.Mapping[str, type],
) -> None:
    definitions = {}

    def add_nested(type_string: str, schema: str):
        type_name = type_string.removeprefix("struct:")
        previous = definitions.get(type_name)
        if previous == schema:
            return

        try:
            database.add(type_name, schema)
            effective_schema = schema
        except UnicodeDecodeError:
            struct_type = nested.get(type_name)
            if struct_type is None or not hasattr(
                struct_type, "__wpistruct_descriptor__"
            ):
                raise
            effective_schema = _native_seed_schema(struct_type)
            try:
                database.add(type_name, effective_schema)
            except UnicodeDecodeError:
                # A Unicode type name cannot be referenced by raw native schema
                # grammar. The unresolved candidate reports the type name below.
                return
        definitions[type_name] = effective_schema

    required_names = {
        field.struct_name
        for field in descriptor.fields
        if field.struct_name is not None
    }
    for type_name in required_names:
        nested_type = nested.get(type_name)
        if nested_type is not None:
            wpistruct.for_each_nested(nested_type, add_nested)


def _make_candidate_descriptor(
    name: str, schema: str, nested: typing.Mapping[str, type]
):
    database = SchemaDatabase()
    descriptor = _add_schema(database, name, schema)
    if not descriptor.is_valid:
        _add_nested_dependency_schemas(database, descriptor, nested)
    return descriptor


def _validate_equivalent_schema(
    name: str, existing_schema: str, candidate_schema: str
) -> None:
    database = SchemaDatabase()
    _add_schema(database, name, existing_schema)
    _stage_schema(database, name, candidate_schema)


def make_wpistruct_from_schema(
    name: str,
    schema: str,
    *,
    nested: typing.Mapping[str, type],
    descriptor=None,
) -> type:
    if descriptor is None:
        descriptor = _make_candidate_descriptor(name, schema, nested)

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
            raise _UnresolvedStructSchema(missing)
        raise ValueError(f"descriptor {name} is not valid")

    class_name = _sanitize_identifier(name.rsplit("::", 1)[-1])
    used_names: set[str] = set()
    fields = []
    python_names = []
    used_enum_names: set[str] = set()
    generated_tuple_elements = 0
    for field in descriptor.fields:
        if field.type != "char" and field.is_array:
            generated_tuple_elements += field.array_size
            if generated_tuple_elements > _MAX_GENERATED_TUPLE_ELEMENTS:
                raise ValueError(
                    "generated wpistruct arrays contain "
                    f"{generated_tuple_elements} total elements; support at most "
                    f"{_MAX_GENERATED_TUPLE_ELEMENTS}"
                )

        field_name = field.name
        if field_name in _GENERATED_ATTRIBUTE_NAMES:
            field_name = f"{field_name}_"
        python_name = _unique_identifier(field_name, used_names)
        annotation = _field_annotation(
            name, field, python_name, nested, used_enum_names
        )
        fields.append((python_name, annotation))
        python_names.append(python_name)

    generated = dataclasses.make_dataclass(
        class_name,
        fields,
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
        self._types: dict[str, type] = {}
        self._definitions: dict[str, str] = {}
        self._supplied_names: set[str] = set()

        supplied_types = tuple(struct_types)
        for struct_type in supplied_types:
            type_name = wpistruct.get_type_name(struct_type)
            existing = self._types.get(type_name)
            if existing is not None and existing is not struct_type:
                raise ValueError(f"duplicate supplied struct type {type_name}")
            self._types[type_name] = struct_type
            self._supplied_names.add(type_name)

        seed_types: dict[str, type] = {}

        def collect_seed_types(struct_type: type) -> None:
            type_name = wpistruct.get_type_name(struct_type)
            if type_name in seed_types:
                return
            seed_types[type_name] = struct_type
            layout = getattr(struct_type, "__wpistruct_descriptor__", None)
            if layout is not None:
                for field in layout.fields:
                    if field.nested_type is not None:
                        collect_seed_types(field.nested_type)

        for struct_type in supplied_types:
            collect_seed_types(struct_type)

        seed_database = SchemaDatabase()

        def add_nested(type_string: str, schema: str):
            type_name = type_string.removeprefix("struct:")
            try:
                seed_database.add(type_name, schema)
                effective_schema = schema
            except UnicodeDecodeError:
                struct_type = seed_types.get(type_name)
                if struct_type is None or not hasattr(
                    struct_type, "__wpistruct_descriptor__"
                ):
                    raise
                effective_schema = _native_seed_schema(struct_type)
                try:
                    seed_database.add(type_name, effective_schema)
                except UnicodeDecodeError:
                    # A Unicode type name cannot be referenced by raw native
                    # schema grammar. Supplied-type lookup still preserves the
                    # authored type's exact public schema and serialization.
                    return
            self._definitions.setdefault(type_name, effective_schema)

        for struct_type in supplied_types:
            wpistruct.for_each_nested(struct_type, add_nested)

    def get(self, type_name: str) -> type | None:
        return self._types.get(type_name)

    def add_schema(self, type_name: str, schema: str) -> type:
        if type_name in self._supplied_names:
            return self._types[type_name]

        existing_schema = self._definitions.get(type_name)
        if existing_schema is not None:
            _validate_equivalent_schema(type_name, existing_schema, schema)

        existing = self._types.get(type_name)
        if existing is not None:
            return existing

        generated = make_wpistruct_from_schema(
            type_name,
            schema,
            nested=self._types,
        )

        self._definitions[type_name] = schema
        self._types[type_name] = generated
        return generated
