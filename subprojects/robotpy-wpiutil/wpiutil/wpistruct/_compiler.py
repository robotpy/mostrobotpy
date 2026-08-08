import collections.abc
import dataclasses
import inspect
import struct
import typing

from .._wpiutil import wpistruct
from .._wpiutil._schema import SchemaDatabase
from .dataclass import (
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


def _resolve_field_plans(cls: type, cls_name: str) -> list[FieldPlan]:
    resolved_hints = typing.get_type_hints(cls, include_extras=True)
    legacy_hints = typing.get_type_hints(cls)
    fields = dataclasses.fields(cls)
    plans = []

    for field_idx, field in enumerate(fields):
        name = field.name
        annotation = resolved_hints[name]
        field_type = legacy_hints[name]
        if field_type in _type_to_fmt:
            fmt, type_name = _type_to_fmt[field_type]
            plans.append(
                FieldPlan(
                    index=field_idx,
                    schema_name=name,
                    python_name=name,
                    annotation=annotation,
                    element_type=field_type,
                    is_array=False,
                    array_size=1,
                    format=fmt,
                    type_name=type_name,
                    nested_type=None,
                )
            )
            continue

        array_info = _get_fixed_tuple_array_info(cls_name, name, field_type)
        if array_info:
            element_type, array_size = array_info
            if element_type in _type_to_fmt:
                fmt, type_name = _type_to_fmt[element_type]
                nested_type = None
            elif hasattr(element_type, "WPIStruct"):
                fmt = None
                type_name = wpistruct.get_type_name(element_type)
                nested_type = element_type
            else:
                raise TypeError(
                    f"{cls_name}.{name} is not a wpistruct or does not have a supported type hint "
                    f"(supported: {_get_supported_type_names()})"
                ) from None

            plans.append(
                FieldPlan(
                    index=field_idx,
                    schema_name=name,
                    python_name=name,
                    annotation=annotation,
                    element_type=element_type,
                    is_array=True,
                    array_size=array_size,
                    format=fmt,
                    type_name=type_name,
                    nested_type=nested_type,
                )
            )
            continue

        if hasattr(field_type, "WPIStruct"):
            plans.append(
                FieldPlan(
                    index=field_idx,
                    schema_name=name,
                    python_name=name,
                    annotation=annotation,
                    element_type=field_type,
                    is_array=False,
                    array_size=1,
                    format=None,
                    type_name=wpistruct.get_type_name(field_type),
                    nested_type=field_type,
                )
            )
            continue

        raise TypeError(
            f"{cls_name}.{name} is not a wpistruct or does not have a supported type hint "
            f"(supported: {_get_supported_type_names()})"
        ) from None

    return plans


def _schema_for_plans(plans: list[FieldPlan]) -> str:
    fields = []
    for plan in plans:
        array_suffix = f"[{plan.array_size}]" if plan.is_array else ""
        fields.append(f"{plan.type_name} {plan.schema_name}{array_suffix}")
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

    fmts = []
    unpackvals = []
    cvvals = []
    vvals = []
    packs = []
    unpacks = []
    for_each_nested = []
    ctx: dict[str, typing.Any] = {"cls": cls}

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
        for_each_nested_statement += (
            f"{padding}raise ValueError(f'{err_name}: error in for_each_nested') from e"
        )

    ctx["_s"] = codec
    function_source = inspect.cleandoc(f"""
        from wpiutil import wpistruct

        def _pack(v):
            try:
                {pack_statements}
                return _s.pack({values})
            except Exception as e:
                raise ValueError(f"{err_name}: error packing data") from e

        def _pack_into(v, b):
            try:
                {pack_statements}
                return _s.pack_into(b, 0, {values})
            except Exception as e:
                raise ValueError(f"{err_name}: error packing data") from e

        def _unpack(b):
            try:
                {unpack_statement}
                {unpack_statements}
                return cls({constructor_values})
            except Exception as e:
                raise ValueError(f"{err_name}: error unpacking data") from e

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

    if descriptor is None:
        descriptor = _make_native_descriptor(struct_name, schema, plans)
    layout = _make_layout(descriptor, plans, python_names)

    cls.WPIStruct = serializer_descriptor
    cls.__wpistruct_descriptor__ = layout
    return cls
