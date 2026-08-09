import dataclasses
import enum
import gc
import typing

import pytest

from wpiutil import wpistruct
import wpiutil.wpistruct._schema as schema_module
from wpiutil.wpistruct._schema import (
    InvalidStructSchema,
    StructTypeRegistry,
    make_wpistruct_from_schema,
)


def test_generate_struct_from_schema():
    generated = make_wpistruct_from_schema(
        "Packet",
        "int32 count; char name[4]; enum {OFF=0,AUTO=1} uint8 mode",
        nested={},
    )
    assert dataclasses.is_dataclass(generated)
    assert wpistruct.get_type_name(generated) == "Packet"
    assert wpistruct.get_schema(generated) == (
        "int32 count; char name[4]; enum {OFF=0,AUTO=1} uint8 mode"
    )
    mode_type = generated.__dataclass_fields__["mode"].type
    value = wpistruct.unpack(generated, b"\x02\0\0\0abc\0\x01")
    assert value.count == 2
    assert value.name == "abc"
    assert isinstance(value.mode, mode_type)
    assert value.mode.name == "AUTO"
    assert wpistruct.pack(value) == b"\x02\0\0\0abc\0\x01"


def test_generated_struct_name_is_not_executed_as_source():
    generated = make_wpistruct_from_schema('Bad"Name', "uint8 value", nested={})
    assert wpistruct.get_type_name(generated) == 'Bad"Name'
    assert wpistruct.unpack(generated, b"\x07") == generated(7)


def test_generated_struct_name_is_always_a_valid_identifier():
    generated = make_wpistruct_from_schema("¼", "uint8 value", nested={})
    assert generated.__name__ == "_"
    assert generated.__name__.isidentifier()
    assert wpistruct.get_type_name(generated) == "¼"
    assert wpistruct.unpack(generated, b"\x07") == generated(7)


def test_generated_nested_struct_and_sanitized_field():
    inner = make_wpistruct_from_schema("Inner", "float32 value", nested={})
    outer = make_wpistruct_from_schema(
        "pkg::Outer", "Inner class; float64 total", nested={"Inner": inner}
    )
    value = wpistruct.unpack(outer, b"\0\0\xc0?\0\0\0\0\0\0\x04@")
    assert value.class_.value == 1.5
    assert value.total == 2.5
    assert wpistruct.get_schema(outer) == "Inner class; float64 total"
    schemas = []
    wpistruct.for_each_nested(
        outer, lambda type_name, schema: schemas.append((type_name, schema))
    )
    assert schemas == [
        ("struct:Inner", "float32 value"),
        ("struct:pkg::Outer", "Inner class; float64 total"),
    ]
    assert outer.__wpistruct_descriptor__.type_name == "pkg::Outer"
    assert outer.__wpistruct_descriptor__.fields[0].schema_name == "class"
    assert outer.__wpistruct_descriptor__.fields[0].python_name == "class_"


def test_generated_fixed_arrays():
    inner = make_wpistruct_from_schema("Inner", "uint8 value", nested={})
    outer = make_wpistruct_from_schema(
        "Outer", "uint16 samples[2]; Inner children[2]", nested={"Inner": inner}
    )
    value = outer((1, 2), (inner(3), inner(4)))
    assert wpistruct.unpack(outer, wpistruct.pack(value)) == value


def test_generated_explicit_singleton_arrays_preserve_tuple_values_and_bytes():
    inner = make_wpistruct_from_schema("SingletonInner", "uint16 value", nested={})
    generated = make_wpistruct_from_schema(
        "GeneratedSingletonArrays",
        "uint8 samples[1]; enum {OFF=0,AUTO=1} uint8 modes[1]; "
        "SingletonInner children[1]",
        nested={"SingletonInner": inner},
    )
    mode_type = typing.get_args(generated.__dataclass_fields__["modes"].type)[0]
    value = generated((7,), (mode_type.AUTO,), (inner(0x1234),))
    encoded = b"\x07\x01\x34\x12"

    assert wpistruct.get_schema(generated) == (
        "uint8 samples[1]; enum {OFF=0,AUTO=1} uint8 modes[1]; "
        "SingletonInner children[1]"
    )
    assert wpistruct.pack(value) == encoded
    assert wpistruct.unpack(generated, encoded) == value
    assert isinstance(value.samples, tuple)
    assert isinstance(value.modes, tuple)
    assert isinstance(value.children, tuple)


def test_many_scalar_fields_do_not_trigger_per_field_schema_scans(monkeypatch):
    scan_calls = 0
    original_compile = schema_module.re.compile
    original_search = schema_module.re.search

    def counting_compile(pattern, *args, **kwargs):
        nonlocal scan_calls
        if isinstance(pattern, str) and "(?P<array>" in pattern:
            scan_calls += 1
        return original_compile(pattern, *args, **kwargs)

    def counting_search(pattern, *args, **kwargs):
        nonlocal scan_calls
        if isinstance(pattern, str) and "(?:enum\\s*)?" in pattern:
            scan_calls += 1
        return original_search(pattern, *args, **kwargs)

    monkeypatch.setattr(schema_module.re, "compile", counting_compile)
    monkeypatch.setattr(schema_module.re, "search", counting_search)
    field_count = 256
    schema = "; ".join(f"uint8 value{i}" for i in range(field_count))

    generated = make_wpistruct_from_schema("ManyScalars", schema, nested={})

    assert len(dataclasses.fields(generated)) == field_count
    assert scan_calls <= 1


def test_generated_array_representability_limit():
    largest = make_wpistruct_from_schema(
        "LargestGeneratedArray", "uint8 values[65536]", nested={}
    )
    assert wpistruct.get_size(largest) == 65536

    with pytest.raises(
        ValueError,
        match=(
            r"generated wpistruct arrays contain 65537 total elements; "
            r"support at most 65536"
        ),
    ):
        make_wpistruct_from_schema(
            "OversizedGeneratedArray", "uint8 values[65537]", nested={}
        )


def test_generated_array_representability_budget_is_cumulative():
    with pytest.raises(
        ValueError,
        match=(
            r"generated wpistruct arrays contain 65538 total elements; "
            r"support at most 65536"
        ),
    ):
        make_wpistruct_from_schema(
            "CumulativelyOversizedGeneratedArrays",
            "uint8 first[32769]; uint8 second[32769]",
            nested={},
        )


def test_generated_empty_schema_and_float_aliases():
    empty = make_wpistruct_from_schema("Empty", "", nested={})
    aliases = make_wpistruct_from_schema(
        "Aliases", "float32 first; float64 second", nested={}
    )
    assert wpistruct.get_size(empty) == 0
    assert wpistruct.unpack(empty, b"") == empty()
    assert wpistruct.get_schema(aliases) == "float32 first; float64 second"
    assert wpistruct.unpack(aliases, wpistruct.pack(aliases(1.5, 2.5))) == aliases(
        1.5, 2.5
    )


def test_generated_identifier_collision_is_deterministic():
    generated = make_wpistruct_from_schema(
        "pkg::Collision", "uint8 class; uint8 class_", nested={}
    )
    assert [field.name for field in dataclasses.fields(generated)] == [
        "class_",
        "class_2",
    ]
    assert [
        field.python_name for field in generated.__wpistruct_descriptor__.fields
    ] == [
        "class_",
        "class_2",
    ]


def test_generated_special_attribute_names_are_sanitized():
    generated = make_wpistruct_from_schema(
        "SpecialFields",
        "uint8 __class__; uint8 __dict__; uint8 __weakref__; "
        "uint8 __dataclass_fields__; uint8 __dataclass_params__; uint8 __match_args__; "
        "uint8 mro; uint8 __module__; uint8 __doc__; uint8 __repr__",
        nested={},
    )
    assert [field.name for field in dataclasses.fields(generated)] == [
        "__class___",
        "__dict___",
        "__weakref___",
        "__dataclass_fields___",
        "__dataclass_params___",
        "__match_args___",
        "mro_",
        "__module___",
        "__doc___",
        "__repr___",
    ]
    value = generated(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    assert wpistruct.unpack(generated, wpistruct.pack(value)) == value


def test_generated_metadata_reservation_does_not_change_other_identifiers():
    generated = make_wpistruct_from_schema(
        "WPIStruct", "enum {WPIStruct=1} uint8 mode", nested={}
    )
    assert generated.__name__ == "WPIStruct"
    mode_type = generated.__dataclass_fields__["mode"].type
    assert list(mode_type.__members__) == ["WPIStruct"]
    assert wpistruct.get_type_name(generated) == "WPIStruct"


def test_generated_serializer_metadata_names_are_sanitized():
    generated = make_wpistruct_from_schema(
        "MetadataFields",
        "uint8 WPIStruct; uint8 WPIStruct_; "
        "uint8 __wpistruct_descriptor__; uint8 __wpistruct_descriptor___",
        nested={},
    )
    assert [field.name for field in dataclasses.fields(generated)] == [
        "WPIStruct_",
        "WPIStruct_2",
        "__wpistruct_descriptor___",
        "__wpistruct_descriptor___2",
    ]
    assert [
        field.schema_name for field in generated.__wpistruct_descriptor__.fields
    ] == [
        "WPIStruct",
        "WPIStruct_",
        "__wpistruct_descriptor__",
        "__wpistruct_descriptor___",
    ]
    value = generated(1, 2, 3, 4)
    assert wpistruct.unpack(generated, wpistruct.pack(value)) == value


def test_generated_enum_class_names_follow_field_collisions():
    generated = make_wpistruct_from_schema(
        "CollisionEnums",
        "enum {A=1} uint8 class; enum {B=2} uint8 class_; "
        "enum {C=3} uint8 mode; enum {D=4} uint8 Mode",
        nested={},
    )
    first = generated.__dataclass_fields__["class_"].type
    second = generated.__dataclass_fields__["class_2"].type
    assert first is not second
    assert first.__name__ == "CollisionEnumsClass_"
    third = generated.__dataclass_fields__["mode"].type
    fourth = generated.__dataclass_fields__["Mode"].type
    assert second.__name__ == "CollisionEnumsClass_2"
    assert third.__name__ == "CollisionEnumsMode"
    assert fourth.__name__ == "CollisionEnumsMode_2"


def test_generated_reserved_enum_names_and_aliases_are_preserved():
    generated = make_wpistruct_from_schema(
        "ReservedEnum",
        "enum {_missing_=1,_missing_member=1,__class__=2,mro=3} uint8 mode",
        nested={},
    )
    mode_type = generated.__dataclass_fields__["mode"].type
    assert list(mode_type.__members__) == [
        "_missing_member",
        "_missing_member_2",
        "__class___member",
        "mro_",
    ]
    assert mode_type._missing_member_2 is mode_type._missing_member
    assert generated.__wpistruct_descriptor__.fields[0].enum_values == (
        ("_missing_", 1),
        ("_missing_member", 1),
        ("__class__", 2),
        ("mro", 3),
    )


@pytest.mark.parametrize("schema", ["{}uint8 mode", "enum{}uint8 mode"])
def test_generated_empty_enum_is_typed(schema):
    generated = make_wpistruct_from_schema("EmptyMode", schema, nested={})
    mode_type = generated.__dataclass_fields__["mode"].type
    assert issubclass(mode_type, enum.IntEnum)
    value = wpistruct.unpack(generated, b"\x07")
    assert isinstance(value.mode, mode_type)
    assert value.mode.name == "UNKNOWN_7"


def test_generated_unknown_enum_is_typed():
    generated = make_wpistruct_from_schema(
        "ModeValue", "enum {OFF=0,AUTO=1} uint8 mode", nested={}
    )
    value = wpistruct.unpack(generated, b"\x07")
    assert isinstance(value.mode, generated.__dataclass_fields__["mode"].type)
    assert value.mode.name == "UNKNOWN_7"
    assert value.mode.value == 7


def test_generated_type_outlives_registry():
    registry = StructTypeRegistry(())
    generated = registry.add_schema("Value", "uint8 value")
    del registry
    gc.collect()
    assert wpistruct.unpack(generated, b"\x07") == generated(7)
    assert wpistruct.pack(generated(8)) == b"\x08"


def test_registry_requires_nested_type_first():
    registry = StructTypeRegistry(())
    with pytest.raises(ValueError, match="Inner.*not registered"):
        registry.add_schema("Outer", "Inner value")


def test_registry_independent_schemas_use_one_native_add_each(monkeypatch):
    native_database = schema_module.SchemaDatabase

    class CountingSchemaDatabase:
        instances = []
        add_calls = []
        stage_calls = []

        def __init__(self, wrapped=None):
            self._wrapped = wrapped or native_database()
            self.instance_adds = []
            type(self).instances.append(self)

        def add(self, type_name, schema):
            self.instance_adds.append(type_name)
            type(self).add_calls.append(type_name)
            return self._wrapped.add(type_name, schema)

        def find(self, type_name):
            return self._wrapped.find(type_name)

        def stage(self, type_name, schema):
            type(self).stage_calls.append(type_name)
            return type(self)(self._wrapped.stage(type_name, schema))

    monkeypatch.setattr(schema_module, "SchemaDatabase", CountingSchemaDatabase)
    registry = StructTypeRegistry(())
    schema_count = 64
    expected_names = [f"Value{index}" for index in range(schema_count)]

    for type_name in expected_names:
        registry.add_schema(type_name, "uint8 value")

    assert CountingSchemaDatabase.stage_calls == []
    assert CountingSchemaDatabase.add_calls == expected_names
    assert [
        database.instance_adds
        for database in CountingSchemaDatabase.instances
        if database.instance_adds
    ] == [[type_name] for type_name in expected_names]


def test_failed_generated_class_construction_does_not_mutate_registry():
    registry = StructTypeRegistry(())

    with pytest.raises(ValueError, match="support at most 65536"):
        registry.add_schema("Value", "uint8 samples[65537]")

    recovered = registry.add_schema("Value", "uint8 value")
    assert wpistruct.unpack(recovered, b"\x07") == recovered(7)


def test_failed_unresolved_registry_schema_does_not_reserve_name():
    registry = StructTypeRegistry(())

    with pytest.raises(ValueError, match="Inner.*not registered"):
        registry.add_schema("Outer", "Inner value")

    recovered = registry.add_schema("Outer", "uint8 value")
    assert wpistruct.get_schema(recovered) == "uint8 value"
    assert wpistruct.unpack(recovered, b"\x07") == recovered(7)


def test_failed_unresolved_registry_schema_can_retry_after_nested_registration():
    registry = StructTypeRegistry(())

    with pytest.raises(ValueError, match="Inner.*not registered"):
        registry.add_schema("Outer", "Inner value")

    inner = registry.add_schema("Inner", "uint8 value")
    outer = registry.add_schema("Outer", "Inner value")
    value = outer(inner(7))
    assert wpistruct.unpack(outer, wpistruct.pack(value)) == value


def test_registry_duplicate_and_conflict_behavior():
    registry = StructTypeRegistry(())
    first = registry.add_schema("Value", "int32 value;")
    assert registry.add_schema("Value", " int32 value ") is first
    with pytest.raises(ValueError, match="conflicting schema for Value"):
        registry.add_schema("Value", "uint32 value")


def test_registry_malformed_schema_is_distinct_error():
    with pytest.raises(InvalidStructSchema, match="expected identifier"):
        StructTypeRegistry(()).add_schema("Bad", "int32 [2]")


def test_direct_generation_preserves_schema_error_taxonomy():
    with pytest.raises(InvalidStructSchema, match="expected identifier"):
        make_wpistruct_from_schema("Bad", "int32 [2]", nested={})

    for schema, match, exception_type in (
        (
            "Missing value",
            "Missing.*not registered",
            schema_module._UnresolvedStructSchema,
        ),
        ("uint8 value; uint8 value", "duplicate field value", ValueError),
    ):
        with pytest.raises(ValueError, match=match) as exc_info:
            make_wpistruct_from_schema("Semantic", schema, nested={})
        assert type(exc_info.value) is exception_type


def test_non_ascii_parser_failures_preserve_schema_error_taxonomy():
    with pytest.raises(InvalidStructSchema):
        make_wpistruct_from_schema("Bad", "uint8 é", nested={})
    with pytest.raises(InvalidStructSchema):
        StructTypeRegistry(()).add_schema("Bad", "uint8 é")


def test_registry_accepts_supplied_nested_unicode_authored_structs():
    inner = dataclasses.make_dataclass(
        "SuppliedUnicodeInner", [("变量", wpistruct.uint16)]
    )
    inner = wpistruct.make_wpistruct(name="SuppliedUnicodeInner")(inner)
    outer = dataclasses.make_dataclass(
        "SuppliedUnicodeOuter", [("π", inner), ("aé", wpistruct.int8)]
    )
    outer = wpistruct.make_wpistruct(name="SuppliedUnicodeOuter")(outer)

    registry = StructTypeRegistry((outer,))

    assert registry.get("SuppliedUnicodeOuter") is outer
    value = outer(inner(0x1234), -2)
    assert wpistruct.unpack(outer, wpistruct.pack(value)) == value


@wpistruct.make_wpistruct(name="Supplied")
@dataclasses.dataclass
class Supplied:
    value: wpistruct.int32


@wpistruct.make_wpistruct(name="Supplied")
@dataclasses.dataclass
class OtherSupplied:
    value: wpistruct.uint32


def test_registry_supplied_type_lookup_and_precedence():
    registry = StructTypeRegistry((Supplied,))
    assert registry.get("Supplied") is Supplied
    assert registry.add_schema("Supplied", "uint32 incompatible") is Supplied


def test_registry_rejects_duplicate_supplied_name_eagerly():
    with pytest.raises(ValueError, match="duplicate supplied struct type Supplied"):
        StructTypeRegistry((Supplied, OtherSupplied))


@wpistruct.make_wpistruct(name="Child")
@dataclasses.dataclass
class Child:
    value: wpistruct.uint8


@wpistruct.make_wpistruct(name="Parent")
@dataclasses.dataclass
class Parent:
    child: Child


@wpistruct.make_wpistruct(name="SeededShapeChild")
@dataclasses.dataclass
class SeededShapeChild:
    value: wpistruct.uint8


@wpistruct.make_wpistruct(name="SeededShapeParent")
@dataclasses.dataclass
class SeededShapeParent:
    child: SeededShapeChild


def test_registry_logged_equivalent_nested_schema_uses_logged_shape():
    registry = StructTypeRegistry((SeededShapeParent,))

    generated = registry.add_schema("SeededShapeChild", "uint8 value[1]")
    value = wpistruct.unpack(generated, b"\x07")

    layout = generated.__wpistruct_descriptor__
    generated_field = generated.__dataclass_fields__["value"]

    assert value.value == (7,)
    assert typing.get_origin(generated_field.type) is tuple
    assert wpistruct.get_schema(generated) == "uint8 value[1]"
    assert layout.schema == "uint8 value[1]"
    assert layout.schema == wpistruct.get_schema(generated)
    assert layout.fields[0].array_size == 1
    assert SeededShapeChild.__wpistruct_descriptor__.schema == "uint8 value"
    assert wpistruct.pack(value) == b"\x07"


def test_registry_seeds_supplied_nested_schemas_child_first():
    registry = StructTypeRegistry((Child, Parent))
    wrapper = registry.add_schema("Wrapper", "Parent parent")
    assert wpistruct.unpack(
        wrapper, wpistruct.pack(wrapper(Parent(Child(3))))
    ) == wrapper(Parent(Child(3)))
