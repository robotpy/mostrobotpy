#pragma once

#include <nanobind/nanobind.h>

#include <vector>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

// ntcore uses std::vector<uint8_t> anytime there is a raw value, so
// add this specialization to convert to/from bytes directly

template<>
struct type_caster<std::vector<uint8_t>> {
    using vector_type = std::vector<uint8_t>;
    NB_TYPE_CASTER(vector_type, const_name("bytes"));

    bool from_python(handle src, uint8_t, cleanup_list *) noexcept {
        if (!PyObject_CheckBuffer(src.ptr())) {
            return false;
        }

        Py_buffer view;
        if (PyObject_GetBuffer(src.ptr(), &view, PyBUF_CONTIG_RO) != 0) {
            PyErr_Clear();
            return false;
        }

        bool ok = view.ndim == 1;
        if (ok) {
            auto begin = static_cast<const uint8_t *>(view.buf);
            value.assign(begin, begin + view.len);
        }

        PyBuffer_Release(&view);
        return ok;
    }

    static handle from_cpp(const std::vector<uint8_t> &src, rv_policy, cleanup_list *) noexcept {
        return nb::bytes(reinterpret_cast<const char *>(src.data()), src.size()).release();
    }
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)
