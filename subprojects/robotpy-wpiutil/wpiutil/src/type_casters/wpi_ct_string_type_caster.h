
#pragma once

#include <nanobind/nanobind.h>

#include <wpi/ct_string.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename CharT, typename Traits, size_t N>
struct type_caster<wpi::ct_string<CharT, Traits, N>> {
    using str_type = wpi::ct_string<CharT, Traits, N>;
    NB_TYPE_CASTER(str_type, const_name("str"));

    // TODO
    bool from_python(handle src, uint8_t, cleanup_list *) noexcept {
        return false;
    }

    static handle from_cpp(const str_type &src, rv_policy,
                           cleanup_list *) noexcept {
        const char *buffer = reinterpret_cast<const char *>(src.data());
        auto nbytes = ssize_t(src.size() * sizeof(CharT));
        return decode_utfN(buffer, nbytes);
    }

    // copied from py::string_caster
    static constexpr size_t UTF_N = 8 * sizeof(CharT);

    static handle decode_utfN(const char *buffer, ssize_t nbytes) {
#if !defined(PYPY_VERSION)
        return UTF_N == 8    ? PyUnicode_DecodeUTF8(buffer, nbytes, nullptr)
               : UTF_N == 16 ? PyUnicode_DecodeUTF16(buffer, nbytes, nullptr, nullptr)
                             : PyUnicode_DecodeUTF32(buffer, nbytes, nullptr, nullptr);
#else
        // PyPy segfaults when on PyUnicode_DecodeUTF16 (and possibly on PyUnicode_DecodeUTF32 as
        // well), so bypass the whole thing by just passing the encoding as a string value, which
        // works properly:
        return PyUnicode_Decode(buffer,
                                nbytes,
                                UTF_N == 8    ? "utf-8"
                                : UTF_N == 16 ? "utf-16"
                                              : "utf-32",
                                nullptr);
#endif
    }

};

// template <typename Char, typename Traits, size_t N>
// struct type_caster<wpi::ct_string<Char, Traits, N>>
//     : string_caster<wpi::ct_string<Char, Traits, N>, false> {};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)
