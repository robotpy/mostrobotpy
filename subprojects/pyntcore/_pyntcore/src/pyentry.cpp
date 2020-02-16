
#include "pyentry.h"
#include "py2value.h"

#include <wpi_arrayref_type_caster.h>
#include <wpi_stringref_type_caster.h>

namespace pyntcore {

py::object GetBooleanEntry(nt::NetworkTableEntry &entry, py::object &defaultValue) {
    std::shared_ptr<nt::Value> value;
    {
        py::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value->type() != NT_BOOLEAN) return defaultValue;
    return py::cast(value->GetBoolean());
}

py::object GetDoubleEntry(nt::NetworkTableEntry &entry, py::object &defaultValue) {
    std::shared_ptr<nt::Value> value;
    {
        py::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value->type() != NT_DOUBLE) return defaultValue;
    return py::cast(value->GetDouble());
}

py::object GetStringEntry(nt::NetworkTableEntry &entry, py::object &defaultValue) {
    std::shared_ptr<nt::Value> value;
    {
        py::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value->type() != NT_STRING) return defaultValue;
    auto s = value->GetString();
    return py::str(s.data(), s.size());
}

py::object GetRawEntry(nt::NetworkTableEntry &entry, py::object &defaultValue) {
    std::shared_ptr<nt::Value> value;
    {
        py::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value->type() != NT_RAW) return defaultValue;
    auto s = value->GetRaw();
    return py::bytes(s.data(), s.size());
}

py::object GetBooleanArrayEntry(nt::NetworkTableEntry &entry, py::object &defaultValue) {
    std::shared_ptr<nt::Value> value;
    {
        py::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value->type() != NT_BOOLEAN_ARRAY) return defaultValue;
    // ntcore will return bit vector by default. Convert to List[bool]
    auto v = value->value();
    py::list l(v.data.arr_boolean.size);
    for (size_t i = 0; i < v.data.arr_boolean.size; i++) {
        auto b = py::bool_(v.data.arr_boolean.arr[i]);
        PyList_SET_ITEM(l.ptr(), i, b.release().ptr());
    }
    return std::move(l);
}

py::object GetDoubleArrayEntry(nt::NetworkTableEntry &entry, py::object &defaultValue) {
    std::shared_ptr<nt::Value> value;
    {
        py::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value->type() != NT_DOUBLE_ARRAY) return defaultValue;
    return py::cast(value->GetDoubleArray());
}

py::object GetStringArrayEntry(nt::NetworkTableEntry &entry, py::object &defaultValue) {
    std::shared_ptr<nt::Value> value;
    {
        py::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value || value->type() != NT_STRING_ARRAY) return defaultValue;
    return py::cast(value->GetStringArray());
}

py::object GetValueEntry(nt::NetworkTableEntry &entry, py::object &defaultValue) {
    std::shared_ptr<nt::Value> value;
    {
        py::gil_scoped_release release;
        value = nt::GetEntryValue(entry.GetHandle());
    }
    if (!value) return defaultValue;
    return ntvalue2py(value.get());
}


}; // pyntcore