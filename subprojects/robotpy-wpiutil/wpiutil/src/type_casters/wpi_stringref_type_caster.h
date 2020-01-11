
#pragma once

#include <pybind11/pybind11.h>

#include <wpi/StringRef.h>

namespace pybind11
{
namespace detail
{

template <>
struct type_caster<wpi::StringRef>
{
public:
    PYBIND11_TYPE_CASTER(wpi::StringRef, _("str"));

    bool load(handle src, bool)
    {
        if (!src || !PyUnicode_Check(src.ptr()))
        {
            return false;
        }

        Py_ssize_t size;
        const char *data = PyUnicode_AsUTF8AndSize(src.ptr(), &size);
        if (data == NULL)
        {
            return false;
        }

        // this assumes that the stringref won't be retained after the function call
        value = wpi::StringRef(data, size);
        return true;
    }

    static handle cast(const wpi::StringRef &s, return_value_policy, handle)
    {
        return PyUnicode_FromStringAndSize(s.data(), s.size());
    }
};

} // namespace detail
} // namespace pybind11