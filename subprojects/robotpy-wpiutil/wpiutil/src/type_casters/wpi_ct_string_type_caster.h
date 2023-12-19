
#pragma once

#include <pybind11/pybind11.h>

#include <wpi/ct_string.h>

namespace pybind11 {
namespace detail {

template <typename Char, typename Traits, size_t N>
struct type_caster<wpi::ct_string<Char, Traits, N>> {
    using str_type = wpi::ct_string<Char, Traits, N>;
    PYBIND11_TYPE_CASTER(str_type, const_name(PYBIND11_STRING_NAME));

    // TODO
    bool load(handle src, bool convert) {
        return false;
    }

    static handle cast(const str_type& src,
                         py::return_value_policy policy,
                         py::handle parent) {
    const char *buffer = reinterpret_cast<const char *>(src.data());
        auto nbytes = ssize_t(src.size() * sizeof(Char));
        handle s;
        if (policy == return_value_policy::_return_as_bytes) {
            s = PyBytes_FromStringAndSize(buffer, nbytes);
        } else {
            s = PyUnicode_DecodeUTF8(buffer, nbytes, nullptr);
        }
        if (!s) {
            throw error_already_set();
        }
        return s;
  }

};

// template <typename Char, typename Traits, size_t N>
// struct type_caster<wpi::ct_string<Char, Traits, N>>
//     : string_caster<wpi::ct_string<Char, Traits, N>, false> {};

} // namespace detail
} // namespace pybind11
