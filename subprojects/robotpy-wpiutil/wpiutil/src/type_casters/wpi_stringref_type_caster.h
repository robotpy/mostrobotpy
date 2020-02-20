
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
            PyErr_Clear();
            return false;
        }

        // this assumes that the stringref won't be retained after the function call
        value = wpi::StringRef(data, size);

        // src must be valid as long as this loader is valid
        loader_life_support::add_patient(src);
        return true;
    }

    static handle cast(const wpi::StringRef &s, return_value_policy, handle)
    {
        handle h = PyUnicode_FromStringAndSize(s.data(), s.size());
        if (!h) throw error_already_set();
        return h;
    }
};

} // namespace detail
} // namespace pybind11