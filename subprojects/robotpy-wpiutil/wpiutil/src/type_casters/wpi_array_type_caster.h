#pragma once

#include <nanobind/nanobind.h>
#include <wpi/array.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <size_t N>
struct wpi_array_name_maker {
  template <typename T>
  static constexpr auto make(const T &t) {
    return concat(t, wpi_array_name_maker<N-1>::make(t));
  }
};

template <>
struct wpi_array_name_maker<1> {
  template <typename T>
  static constexpr auto make(const T &t) {
    return t;
  }
};

// inspired by nanobind/stl/pair.h, nanobind/stl/detail/nb_array.h, nanobind/stl/tuple.h
template <typename Entry, size_t Size>
struct type_caster<wpi::array<Entry, Size>> {

    using Value = wpi::array<Entry, Size>;
    using Caster = make_caster<Entry>;

    /// This caster constructs instances on the fly. Because of this, only the
    /// `operator Value()` cast operator is implemented below, and the type
    /// alias below informs users of this class of this fact.
    template <typename T> using Cast = Value;

    static constexpr auto Name = io_name("collections.abc.Sequence", "tuple") + const_name("[") + wpi_array_name_maker<Size>::make(make_caster<Entry>::Name) + const_name("]");

    Caster casters[Size];

    /// Python -> C++ caster, populates `casters` upon success
    bool from_python(handle src, uint8_t flags,
                     cleanup_list *cleanup) noexcept {
        PyObject *temp;
        PyObject **o = seq_get_with_size(src.ptr(), Size, &temp);
    
        bool success = o != nullptr;
        if (success) {
            for (size_t i = 0; i < Size; ++i) {
                if (!casters[i].from_python(o[i], flags, cleanup)) {
                    success = false;
                    break;
                }
            }
        }

        Py_XDECREF(temp);

        return success;
    }

    template <typename T>
    static handle from_cpp(T *value, rv_policy policy, cleanup_list *cleanup) {
        if (!value)
            return none().release();
        return from_cpp(*value, policy, cleanup);
    }

    template <typename T>
    static handle from_cpp(T &&src, rv_policy policy, cleanup_list *cleanup) {
        object o[Size];
        Py_ssize_t index = 0;

        for (auto &&value : src) {
            handle h = Caster::from_cpp(forward_like_<T>(value), policy, cleanup);

            if (!h.is_valid()) {
                return handle();
            }

            o[index++] = steal(h); 
        }

        PyObject *r = PyTuple_New(Size);
        for (size_t i = 0; i < Size; i++) {
            NB_TUPLE_SET_ITEM(r, i, o[i].release().ptr());
        }
        return r;
    }

    template <typename T>
    bool can_cast() const noexcept {
        for (size_t i = 0; i < Size; i++) {
            if (!casters[i].template can_cast<T>()) {
                return false;
            }
        }
        return true;
    }

    /// Return the constructed tuple by copying from the sub-casters
    explicit operator Value() {
        Value value{wpi::empty_array_t{}};
        for (size_t i = 0; i < Size; i++) {
            value[i] = casters[i].operator cast_t<Entry>();
        }
        return value;
    }
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)
