
#pragma once

#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>

#include <wpi/SmallVector.h>
#include <span>

// portions from
// - nanobind/stl/nb_array.h
// - nanobind/stl/nb_list.h



NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <size_t N>
struct span_name_maker {
    template <typename T>
    static constexpr auto make(const T &t) {
        return concat(t, span_name_maker<N-1>::make(t));
    }
};

template <>
struct span_name_maker<1> {
    template <typename T>
    static constexpr auto make(const T &t) {
        return t;
    }
};

// span with fixed size converts to a tuple
template <typename Type, size_t Extent> struct type_caster<std::span<Type, Extent>> {
    using span_type = typename std::span<Type, Extent>;
    using Caster = make_caster<Type>;
    using value_type = typename std::remove_cv<Type>::type;

    value_type backing_array[Extent] = {};

    NB_TYPE_CASTER(span_type, io_name("collections.abc.Sequence", "tuple") + const_name("[") + span_name_maker<Extent>::make(Caster::Name) + const_name("]"));

    type_caster() : value(backing_array) {}
    
    
    bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept {
        PyObject *temp;

        /* Will initialize 'temp' (NULL in the case of a failure.) */
        PyObject **o = seq_get_with_size(src.ptr(), Extent, &temp);

        Caster caster;
        bool success = o != nullptr;

        flags = flags_for_local_caster<Type>(flags);

        if (success) {
            for (size_t i = 0; i < Extent; ++i) {
                if (!caster.from_python(o[i], flags, cleanup) ||
                    !caster.template can_cast<Type>()) {
                    success = false;
                    break;
                }

                backing_array[i] = caster.operator cast_t<Type>();
            }
        }

        Py_XDECREF(temp);

        return success;
    }

    template <typename T>
    static handle from_cpp(T &&src, rv_policy policy, cleanup_list *cleanup) noexcept {
        object o[Extent];
        Py_ssize_t index = 0;

        for (auto &&value : src) {
            handle h = Caster::from_cpp(forward_like_<T>(value), policy, cleanup);

            if (!h.is_valid()) {
                return handle();
            }

            o[index++] = steal(h); 
        }

        PyObject *r = PyTuple_New(Extent);
        for (size_t i = 0; i < Extent; i++) {
            NB_TUPLE_SET_ITEM(r, i, o[i].release().ptr());
        }
        return r;
    }
};


// span with dynamic extent
template <typename Type> struct type_caster<std::span<Type, std::dynamic_extent>> {
    using span_type = typename  std::span<Type, std::dynamic_extent>;
    using Caster = make_caster<Type>;
    using value_type = typename std::remove_cv<Type>::type;

    wpi::SmallVector<value_type, 32> vec;

    NB_TYPE_CASTER(span_type, io_name("collections.abc.Sequence", "list") + const_name("[") + Caster::Name + const_name("]"));

    type_caster() : vec(0), value(vec) {}

    bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept {
        size_t size;
        PyObject *temp;

        /* Will initialize 'size' and 'temp'. All return values and
           return parameters are zero/NULL in the case of a failure. */
        PyObject **o = seq_get(src.ptr(), &size, &temp);

        vec.clear();
        vec.reserve(size);

        Caster caster;
        bool success = o != nullptr;

        flags = flags_for_local_caster<Type>(flags);
        
        for (size_t i = 0; i < size; ++i) {
            if (!caster.from_python(o[i], flags, cleanup) ||
                !caster.template can_cast<Type>()) {
                success = false;
                break;
            }

            vec.push_back(caster.operator cast_t<Type>());
        }

        Py_XDECREF(temp);

        value = span_type(std::data(vec), std::size(vec));
        return success;
    }

    template <typename T>
    static handle from_cpp(T &&src, rv_policy policy, cleanup_list *cleanup) noexcept {
        object ret = steal(PyList_New(src.size()));

        if (ret.is_valid()) {
            Py_ssize_t index = 0;

            for (auto &&value : src) {
                handle h = Caster::from_cpp(forward_like_<T>(value), policy, cleanup);

                if (!h.is_valid()) {
                    ret.reset();
                    break;
                }

                NB_LIST_SET_ITEM(ret.ptr(), index++, h.ptr());
            }
        }

        return ret.release();
    }
};

// span specialization: accepts any readonly buffers
template <> struct type_caster<std::span<const uint8_t, std::dynamic_extent>> {
    using span_type = typename std::span<const uint8_t, std::dynamic_extent>;
    using array_type = ndarray<const uint8_t, shape<-1>, device::cpu, c_contig>;
    using Caster = make_caster<array_type>;

    // the @__@__@ thing is what io_name does, but it only accepts const char
    NB_TYPE_CASTER(span_type, const_name('@') + Caster::Name + const_name("@bytes@"));

    Caster caster;

    bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept {
        if (!caster.from_python(src, flags, cleanup)) {
            return false;
        }

        value = span_type(caster.value.data(), caster.value.size());
        return true;
    }

    template <typename T>
    static handle from_cpp(T &&src, rv_policy policy, cleanup_list *cleanup) noexcept {
        return PyBytes_FromStringAndSize((const char*)src.data(), src.size());
    }
};

// span specialization: writeable buffer
template <> struct type_caster<std::span<uint8_t, std::dynamic_extent>> {
    using span_type = typename std::span<uint8_t, std::dynamic_extent>;
    using array_type = ndarray<uint8_t, shape<-1>, device::cpu, c_contig>;
    using Caster = make_caster<array_type>;

    // the @__@__@ thing is what io_name does, but it only accepts const char
    NB_TYPE_CASTER(span_type, const_name('@') + Caster::Name + const_name("@bytes@"));

    Caster caster;

    bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept {
        if (!caster.from_python(src, flags, cleanup)) {
            return false;
        }

        value = span_type(caster.value.data(), caster.value.size());
        return true;
    }

    template <typename T>
    static handle from_cpp(T &&src, rv_policy policy, cleanup_list *cleanup) noexcept {
        // TODO: should this be a memoryview instead?
        return PyBytes_FromStringAndSize((const char*)src.data(), src.size());
    }
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)
