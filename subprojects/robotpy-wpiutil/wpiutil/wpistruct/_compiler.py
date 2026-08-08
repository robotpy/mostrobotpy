import collections.abc
import dataclasses
import enum
import inspect
import struct
import typing

from .._wpiutil import wpistruct
from .._wpiutil._schema import SchemaDatabase, pack_schema, unpack_schema
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
from .desc import StructDescriptor
from .layout import StructFieldLayout, StructLayout

_type_to_fmt = {
    bool: ("?", "bool"),
    int8: ("b", "int8"),
    uint8: ("B", "uint8"),
    int16: ("h", "int16"),
    uint16: ("H", "uint16"),
    int: ("i", "int32"),
    int32: ("i", "int32"),
    uint32: ("I", "uint32"),
    int64: ("q", "int64"),
    uint64: ("Q", "uint64"),
    float: ("f", "float"),
    double: ("d", "double"),
}
_sized_integer_types = (int8, uint8, int16, uint16, int32, uint32, int64, uint64)
_signed_integer_types = (int8, int16, int32, int64)


@dataclasses.dataclass(slots=True)
class FieldPlan:
    index: int
    schema_name: str
    python_name: str
    annotation: type
    element_type: type
    is_array: bool
    array_size: int
    format: str | None
    type_name: str
    nested_type: type | None
    bit_width: int | None = None
    enum_type: type[enum.IntEnum] | None = None
    enum_cache: dict[int, enum.IntEnum] = dataclasses.field(default_factory=dict)
    is_char: bool = False


def _get_supported_type_names():
    supported_names = ", ".join(t.__name__ for t in _type_to_fmt.keys())
    return f"{supported_names}, or fixed-length homogeneous tuple of a supported type"


def _get_fixed_tuple_array_info(cls_name: str, field_name: str, field_type: type):
    origin = typing.get_origin(field_type)
    if origin is not tuple:
        return None

    args = typing.get_args(field_type)
    if not args or args[-1] is Ellipsis:
        raise TypeError(
            f"{cls_name}.{field_name} has unsupported tuple type hint: "
            "tuple fields must be fixed-length and homogeneous"
        ) from None

    element_type = args[0]
    if not all(arg == element_type for arg in args):
        raise TypeError(
            f"{cls_name}.{field_name} has unsupported tuple type hint: "
            "tuple fields must be fixed-length and homogeneous"
        ) from None

    return element_type, len(args)


def _class_name(cls: type) -> str:
    name_parts = [
        getattr(cls, "__module__", None),
        getattr(cls, "__qualname__", cls.__name__),
    ]
    return ".".join(name for name in name_parts if name)


def _split_annotated(annotation: type):
    if typing.get_origin(annotation) is typing.Annotated:
        base_type, *metadata = typing.get_args(annotation)
        return base_type, metadata
    return annotation, []


def _is_int_enum(field_type: type) -> bool:
    return isinstance(field_type, type) and issubclass(field_type, enum.IntEnum)


def _integer_range(field_type: type, bit_width: int | None = None):
    width = bit_width
    if width is None:
        width = struct.calcsize(_type_to_fmt[field_type][0]) * 8
    if field_type in _signed_integer_types:
        return -(2 ** (width - 1)), 2 ** (width - 1) - 1
    return 0, 2**width - 1


def _unsupported_field(cls_name: str, field_name: str):
    raise TypeError(
        f"{cls_name}.{field_name} is not a wpistruct or does not have a supported type hint "
        f"(supported: {_get_supported_type_names()})"
    ) from None


def _resolve_field_plan(
    cls_name: str,
    field_idx: int,
    field_name: str,
    annotation: type,
    legacy_type: type,
) -> FieldPlan:
    _, metadata = _split_annotated(annotation)
    field_type = legacy_type
    char_arrays = [item for item in metadata if isinstance(item, CharArray)]
    bitfields = [item for item in metadata if isinstance(item, BitField)]
    storage_types = [
        item
        for item in metadata
        if any(item is storage_type for storage_type in _sized_integer_types)
    ]

    if len(char_arrays) > 1:
        raise TypeError(f"{cls_name}.{field_name} has multiple CharArray metadata")
    if len(bitfields) > 1:
        raise TypeError(f"{cls_name}.{field_name} has multiple bitfield metadata")
    if len(storage_types) > 1:
        raise TypeError(
            f"{cls_name}.{field_name} has multiple storage types for enum field"
        )

    bit_width = bitfields[0].width if bitfields else None
    if char_arrays:
        if field_type is not str:
            raise TypeError(
                f"{cls_name}.{field_name} CharArray metadata is only valid on str"
            )
        if bit_width is not None:
            raise TypeError(f"{cls_name}.{field_name} array cannot be bitfield")
        if storage_types:
            raise TypeError(
                f"{cls_name}.{field_name} integer storage is only valid on enum fields"
            )
        return FieldPlan(
            index=field_idx,
            schema_name=field_name,
            python_name=field_name,
            annotation=annotation,
            element_type=str,
            is_array=True,
            array_size=char_arrays[0].size,
            format=None,
            type_name="char",
            nested_type=None,
            is_char=True,
        )

    array_info = _get_fixed_tuple_array_info(cls_name, field_name, field_type)
    if array_info:
        element_type, array_size = array_info
        is_array = True
    else:
        element_type = field_type
        array_size = 1
        is_array = False

    enum_type = element_type if _is_int_enum(element_type) else None
    if enum_type is not None:
        if not storage_types:
            raise TypeError(
                f"{cls_name}.{field_name} enum requires sized integer storage"
            )
        storage_type = storage_types[0]
        fmt, storage_name = _type_to_fmt[storage_type]
        enum_values = ",".join(
            f"{member_name}={member.value}"
            for member_name, member in enum_type.__members__.items()
        )
        type_name = f"enum {{{enum_values}}} {storage_name}"
        nested_type = None
    else:
        if storage_types:
            raise TypeError(
                f"{cls_name}.{field_name} integer storage is only valid on enum fields"
            )
        storage_type = element_type
        if element_type in _type_to_fmt:
            fmt, type_name = _type_to_fmt[element_type]
            nested_type = None
        elif hasattr(element_type, "WPIStruct"):
            fmt = None
            type_name = wpistruct.get_type_name(element_type)
            nested_type = element_type
        elif element_type is char and not is_array:
            fmt = None
            type_name = "char"
            nested_type = None
        else:
            _unsupported_field(cls_name, field_name)

    if bit_width is not None:
        if is_array:
            raise TypeError(f"{cls_name}.{field_name} array cannot be bitfield")
        if enum_type is not None:
            bitfield_type = storage_type
        else:
            bitfield_type = element_type
        if bitfield_type is bool:
            if bit_width != 1:
                raise TypeError(
                    f"{cls_name}.{field_name} bool bitfield width must be 1"
                )
        elif bitfield_type in _sized_integer_types:
            type_width = struct.calcsize(_type_to_fmt[bitfield_type][0]) * 8
            if bit_width > type_width:
                raise TypeError(
                    f"{cls_name}.{field_name} bitfield width {bit_width} exceeds type size"
                )
        else:
            raise TypeError(
                f"{cls_name}.{field_name} type {getattr(element_type, '__name__', element_type)} "
                "cannot be bitfield"
            )

    if enum_type is not None:
        minimum, maximum = _integer_range(storage_type, bit_width)
        for member_name, member in enum_type.__members__.items():
            if member.value < minimum or member.value > maximum:
                raise TypeError(
                    f"{cls_name}.{field_name} enum member {member_name}={member.value} "
                    f"does not fit storage range {minimum} to {maximum}"
                )

    return FieldPlan(
        index=field_idx,
        schema_name=field_name,
        python_name=field_name,
        annotation=annotation,
        element_type=element_type,
        is_array=is_array,
        array_size=array_size,
        format=fmt,
        type_name=type_name,
        nested_type=nested_type,
        bit_width=bit_width,
        enum_type=enum_type,
        is_char=element_type is char,
    )


def _resolve_field_plans(cls: type, cls_name: str) -> list[FieldPlan]:
    resolved_hints = typing.get_type_hints(cls, include_extras=True)
    legacy_hints = typing.get_type_hints(cls)
    return [
        _resolve_field_plan(
            cls_name,
            field_idx,
            field.name,
            resolved_hints[field.name],
            legacy_hints[field.name],
        )
        for field_idx, field in enumerate(dataclasses.fields(cls))
    ]


def _schema_for_plans(plans: list[FieldPlan]) -> str:
    fields = []
    for plan in plans:
        array_suffix = f"[{plan.array_size}]" if plan.is_array else ""
        bitfield_suffix = f":{plan.bit_width}" if plan.bit_width is not None else ""
        fields.append(
            f"{plan.type_name} {plan.schema_name}{array_suffix}{bitfield_suffix}"
        )
    return "; ".join(fields)


def _make_native_descriptor(struct_name: str, schema: str, plans: list[FieldPlan]):
    database = SchemaDatabase()
    schemas: dict[str, str] = {}

    def add_nested(type_string: str, nested_schema: str):
        nested_name = type_string.removeprefix("struct:")
        if schemas.get(nested_name) == nested_schema:
            return
        database.add(nested_name, nested_schema)
        schemas[nested_name] = nested_schema

    for plan in plans:
        if plan.nested_type is not None:
            wpistruct.for_each_nested(plan.nested_type, add_nested)

    return database.add(struct_name, schema)


def _layout_python_names(native_fields, plans, python_names):
    if python_names is None:
        return tuple(plan.python_name for plan in plans)
    if isinstance(python_names, collections.abc.Mapping):
        return tuple(python_names[field.name] for field in native_fields)
    return tuple(python_names)


def _make_layout(native_descriptor, plans, python_names) -> StructLayout:
    native_fields = native_descriptor.fields
    layout_names = _layout_python_names(native_fields, plans, python_names)
    fields = tuple(
        StructFieldLayout(
            schema_name=field.name,
            python_name=python_name,
            type_name=field.type,
            offset=field.offset,
            size=field.size,
            array_size=field.array_size,
            bit_width=field.bit_width,
            bit_shift=field.bit_shift,
            bit_mask=field.bit_mask,
            enum_values=tuple(field.enum_values),
            nested_type=plan.nested_type,
        )
        for field, plan, python_name in zip(
            native_fields, plans, layout_names, strict=True
        )
    )
    return StructLayout(
        type_name=native_descriptor.name,
        schema=native_descriptor.schema,
        size=native_descriptor.size,
        fields=fields,
    )


def _make_legacy_layout(
    struct_name: str, schema: str, plans: list[FieldPlan]
) -> StructLayout:
    offset = 0
    fields = []
    for plan in plans:
        if plan.nested_type is not None:
            field_size = wpistruct.get_size(plan.nested_type)
            bit_width = 0
            bit_mask = 0
        else:
            field_size = struct.calcsize(typing.cast(str, plan.format))
            bit_width = field_size * 8
            bit_mask = (1 << bit_width) - 1
        fields.append(
            StructFieldLayout(
                schema_name=plan.schema_name,
                python_name=plan.python_name,
                type_name=plan.type_name,
                offset=offset,
                size=field_size,
                array_size=plan.array_size,
                bit_width=bit_width,
                bit_shift=0,
                bit_mask=bit_mask,
                enum_values=(),
                nested_type=plan.nested_type,
            )
        )
        offset += field_size * plan.array_size
    return StructLayout(
        type_name=struct_name,
        schema=schema,
        size=offset,
        fields=tuple(fields),
    )


def _enum_from_int(
    enum_type: type[enum.IntEnum], value: int, cache: dict[int, enum.IntEnum]
) -> enum.IntEnum:
    member = enum_type._value2member_map_.get(value)
    if member is not None:
        return member

    member = cache.get(value)
    if member is None:
        member = int.__new__(enum_type, value)
        member._name_ = f"UNKNOWN_{value}"
        member._value_ = value
        cache[value] = member
    return member


def _descriptor_pack_element(plan: FieldPlan, value):
    if plan.enum_type is not None:
        if not isinstance(value, plan.enum_type):
            raise TypeError(
                f"field {plan.python_name} must be a {plan.enum_type.__name__} instance"
            )
        return int(value)
    if plan.nested_type is not None:
        return wpistruct.pack(value)
    return value


def _descriptor_pack_value(plan: FieldPlan, value):
    if plan.is_char:
        return value
    if plan.is_array:
        values = tuple(_descriptor_pack_element(plan, item) for item in value)
        if len(values) != plan.array_size:
            raise ValueError(
                f"field {plan.python_name} must contain {plan.array_size} values"
            )
        if plan.array_size == 1:
            return values[0]
        return values
    return _descriptor_pack_element(plan, value)


def _descriptor_unpack_element(plan: FieldPlan, value):
    if plan.enum_type is not None:
        return _enum_from_int(plan.enum_type, value, plan.enum_cache)
    if plan.nested_type is not None:
        return wpistruct.unpack(plan.nested_type, value)
    return value


def _descriptor_unpack_value(plan: FieldPlan, value):
    if plan.is_char:
        if plan.is_array:
            return value
        return char(value or "\0")
    if plan.is_array:
        values = (value,) if plan.array_size == 1 else value
        return tuple(_descriptor_unpack_element(plan, item) for item in values)
    return _descriptor_unpack_element(plan, value)


def _make_descriptor_serializer(
    cls: type,
    struct_name: str,
    schema: str,
    err_name: str,
    plans: list[FieldPlan],
    descriptor,
) -> StructDescriptor:
    def pack_data(value):
        values = tuple(
            _descriptor_pack_value(plan, getattr(value, plan.python_name))
            for plan in plans
        )
        return pack_schema(descriptor, values)

    def pack(value):
        try:
            return pack_data(value)
        except Exception as exc:
            raise ValueError(f"{err_name}: error packing data") from exc

    def pack_into(value, buffer):
        try:
            encoded = pack_data(value)
            destination = memoryview(buffer).cast("B")
            if destination.nbytes < len(encoded):
                raise ValueError(
                    f"pack_into requires a buffer of at least {len(encoded)} bytes"
                )
            destination[: len(encoded)] = encoded
        except Exception as exc:
            raise ValueError(f"{err_name}: error packing data") from exc

    def unpack(buffer):
        try:
            values = unpack_schema(descriptor, buffer)
            converted = (
                _descriptor_unpack_value(plan, value)
                for plan, value in zip(plans, values, strict=True)
            )
            return cls(*converted)
        except Exception as exc:
            raise ValueError(f"{err_name}: error unpacking data") from exc

    nested_types = [plan.nested_type for plan in plans if plan.nested_type is not None]
    if nested_types:

        def for_each_nested(fn):
            try:
                for nested_type in nested_types:
                    wpistruct.for_each_nested(nested_type, fn)
            except Exception as exc:
                raise ValueError(f"{err_name}: error in for_each_nested") from exc

    else:
        for_each_nested = None

    return StructDescriptor(
        typename=struct_name,
        schema=schema,
        size=descriptor.size,
        pack=pack,
        pack_into=pack_into,
        unpack=unpack,
        for_each_nested=for_each_nested,
    )


def compile_wpistruct(
    cls,
    struct_name,
    *,
    schema_override=None,
    descriptor=None,
    python_names=None,
) -> type:
    cls_name = _class_name(cls)
    if struct_name is None:
        struct_name = cls.__name__
        err_name = cls_name
    else:
        err_name = f"{struct_name} ({cls_name})"

    plans = _resolve_field_plans(cls, cls_name)
    schema = (
        schema_override if schema_override is not None else _schema_for_plans(plans)
    )
    use_descriptor_codec = any(
        plan.is_char or plan.enum_type is not None or plan.bit_width is not None
        for plan in plans
    )
    legacy_layout = None
    if descriptor is None:
        try:
            descriptor = _make_native_descriptor(struct_name, schema, plans)
        except UnicodeDecodeError:
            if schema_override is not None or use_descriptor_codec:
                raise
            # The native parser accepts only ASCII identifiers, while legacy
            # authored dataclasses have always accepted Python's Unicode
            # identifiers. Their packed layout is the legacy struct.Struct
            # layout, so construct equivalent immutable metadata without
            # changing the public schema or serialization path.
            legacy_layout = _make_legacy_layout(struct_name, schema, plans)

    if use_descriptor_codec:
        serializer_descriptor = _make_descriptor_serializer(
            cls, struct_name, schema, err_name, plans, descriptor
        )
        layout = _make_layout(descriptor, plans, python_names)
        cls.WPIStruct = serializer_descriptor
        cls.__wpistruct_descriptor__ = layout
        return cls

    fmts = []
    unpackvals = []
    cvvals = []
    vvals = []
    packs = []
    unpacks = []
    for_each_nested = []
    # Pack/unpack functions retain this globals dictionary, keeping the native
    # descriptor database alive with the generated class.
    ctx: dict[str, typing.Any] = {
        "cls": cls,
        "descriptor": descriptor,
        "_err_name": err_name,
    }

    for plan in plans:
        name = plan.python_name
        if plan.is_array:
            argn = f"arg_{name}"
            unpack_args = [
                f"arg{plan.index}_{item_idx}" for item_idx in range(plan.array_size)
            ]
            if plan.nested_type is None:
                fmts.append(f"{plan.array_size}{plan.format}")
                unpackvals.extend(unpack_args)
                cvvals.append(argn)
                vvals.append(f"*v.{name}")
                unpacks.append(f"{argn} = ({', '.join(unpack_args)},)")
            else:
                typn = f"type_{name}"
                ctx[typn] = plan.nested_type
                size = wpistruct.get_size(plan.nested_type)
                fmts.extend(f"{size}s" for _ in range(plan.array_size))
                unpackvals.extend(unpack_args)
                vvals.append(f"*{argn}")
                cvvals.append(argn)
                packs.append(f"{argn} = tuple(wpistruct.pack(i) for i in v.{name})")
                unpack_exprs = [
                    f"wpistruct.unpack({typn}, {arg})" for arg in unpack_args
                ]
                unpacks.append(f"{argn} = ({', '.join(unpack_exprs)},)")
                for_each_nested.append(f"wpistruct.for_each_nested({typn}, fn)")
        elif plan.nested_type is not None:
            argn = f"arg_{name}"
            typn = f"type_{name}"
            ctx[typn] = plan.nested_type
            size = wpistruct.get_size(plan.nested_type)
            fmts.append(f"{size}s")
            vvals.append(argn)
            unpackvals.append(argn)
            cvvals.append(argn)
            packs.append(f"{argn} = wpistruct.pack(v.{name})")
            unpacks.append(f"{argn} = wpistruct.unpack({typn}, {argn})")
            for_each_nested.append(f"wpistruct.for_each_nested({typn}, fn)")
        else:
            fmts.append(typing.cast(str, plan.format))
            unpackvals.append(f"arg_{name}")
            cvvals.append(f"arg_{name}")
            vvals.append(f"v.{name}")

    codec = struct.Struct(f"<{''.join(fmts)}")
    unpack_values = ", ".join(unpackvals)
    if len(unpackvals) == 1:
        unpack_values += ","
    if unpack_values:
        unpack_statement = f"{unpack_values} = _s.unpack(b)"
    else:
        unpack_statement = "_s.unpack(b)"
    constructor_values = ", ".join(cvvals)
    values = ", ".join(vvals)

    padding = "\n" + " " * 16
    pack_statements = padding.join(packs)
    unpack_statements = padding.join(unpacks)

    if not for_each_nested:
        for_each_nested_statement = "_for_each_nested = None"
    else:
        for_each_nested_statement = "def _for_each_nested(fn):"
        for_each_nested_statement += "\n" + " " * 12
        for_each_nested_statement += f"try:{padding}"
        for_each_nested_statement += padding.join(for_each_nested)
        for_each_nested_statement += "\n" + " " * 12
        for_each_nested_statement += "except Exception as e:"
        for_each_nested_statement += f"{padding}raise ValueError(f'{{_err_name}}: error in for_each_nested') from e"

    ctx["_s"] = codec
    function_source = inspect.cleandoc(f"""
        from wpiutil import wpistruct

        def _pack(v):
            try:
                {pack_statements}
                return _s.pack({values})
            except Exception as e:
                raise ValueError(f"{{_err_name}}: error packing data") from e

        def _pack_into(v, b):
            try:
                {pack_statements}
                return _s.pack_into(b, 0, {values})
            except Exception as e:
                raise ValueError(f"{{_err_name}}: error packing data") from e

        def _unpack(b):
            try:
                {unpack_statement}
                {unpack_statements}
                return cls({constructor_values})
            except Exception as e:
                raise ValueError(f"{{_err_name}}: error unpacking data") from e

        {for_each_nested_statement}
    """)
    exec(function_source, ctx, ctx)

    serializer_descriptor = StructDescriptor(
        typename=struct_name,
        schema=schema,
        size=codec.size,
        pack=ctx["_pack"],
        pack_into=ctx["_pack_into"],
        unpack=ctx["_unpack"],
        for_each_nested=ctx["_for_each_nested"],
    )

    layout = (
        legacy_layout
        if legacy_layout is not None
        else _make_layout(descriptor, plans, python_names)
    )

    cls.WPIStruct = serializer_descriptor
    cls.__wpistruct_descriptor__ = layout
    return cls
