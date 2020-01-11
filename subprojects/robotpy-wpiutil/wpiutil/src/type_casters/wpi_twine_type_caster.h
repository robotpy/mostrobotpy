
#pragma once

#include <pybind11/pybind11.h>

#include <wpi/StringRef.h>
#include <wpi/Twine.h>

namespace pybind11
{
namespace detail
{

template <>
struct type_caster<wpi::Twine>
{
public:
    // initialize the twine to point at the underlying StringRef
    // which we use to store the data
    type_caster() : value(ref) {}

    PYBIND11_TYPE_CASTER(wpi::Twine, _("str"));

    wpi::StringRef ref;

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
        ref = wpi::StringRef(data, size);
        return true;
    }

    static handle cast(const wpi::Twine &t, return_value_policy, handle)
    {
        throw py::cast_error("wpi::Twine should never be a return value");
    }
};

} // namespace detail
} // namespace pybind11