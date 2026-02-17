
#include "pyentry.h"
#include "py2value.h"

#include <pybind11/stl.h>
#include <wpi_span_type_caster.h>

namespace pyntcore {

nb::object GetBooleanEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue) {
    nt::Value value;
    {
        nb::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value.type() != NT_BOOLEAN) return defaultValue;
    return nb::cast(value.GetBoolean());
}

nb::object GetDoubleEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue) {
    nt::Value value;
    {
        nb::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value.type() != NT_DOUBLE) return defaultValue;
    return nb::cast(value.GetDouble());
}

nb::object GetFloatEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue) {
    nt::Value value;
    {
        nb::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value.type() != NT_FLOAT) return defaultValue;
    return nb::cast(value.GetFloat());
}

nb::object GetIntegerEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue) {
    nt::Value value;
    {
        nb::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value.type() != NT_INTEGER) return defaultValue;
    return nb::cast(value.GetInteger());
}


nb::object GetStringEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue) {
    nt::Value value;
    {
        nb::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value.type() != NT_STRING) return defaultValue;
    auto s = value.GetString();
    return nb::str(s.data(), s.size());
}

nb::object GetRawEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue) {
    nt::Value value;
    {
        nb::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value.type() != NT_RAW) return defaultValue;
    return nb::cast(value.GetRaw());
}

nb::object GetBooleanArrayEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue) {
    nt::Value value;
    {
        nb::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value.type() != NT_BOOLEAN_ARRAY) return defaultValue;
    // ntcore will return bit vector by default. Convert to List[bool]
    auto v = value.value();
    nb::list l(v.data.arr_boolean.size);
    for (size_t i = 0; i < v.data.arr_boolean.size; i++) {
        auto b = nb::bool_(v.data.arr_boolean.arr[i]);
        PyList_SET_ITEM(l.ptr(), i, b.release().ptr());
    }
    return std::move(l);
}

nb::object GetDoubleArrayEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue) {
    nt::Value value;
    {
        nb::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value.type() != NT_DOUBLE_ARRAY) return defaultValue;
    return nb::cast(value.GetDoubleArray());
}

nb::object GetFloatArrayEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue) {
    nt::Value value;
    {
        nb::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value.type() != NT_FLOAT_ARRAY) return defaultValue;
    return nb::cast(value.GetFloatArray());
}

nb::object GetIntegerArrayEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue) {
    nt::Value value;
    {
        nb::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value.type() != NT_INTEGER_ARRAY) return defaultValue;
    return nb::cast(value.GetIntegerArray());
}

nb::object GetStringArrayEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue) {
    nt::Value value;
    {
        nb::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value.type() != NT_STRING_ARRAY) return defaultValue;
    std::span<const std::string> rval = value.GetStringArray();
    return nb::cast(rval);
}

nb::object GetValueEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue) {
    nt::Value value;
    {
        nb::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value) return defaultValue;
    return ntvalue2py(value);
}


}; // pyntcore
