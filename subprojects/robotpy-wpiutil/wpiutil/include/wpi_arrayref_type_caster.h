
#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <wpi/ArrayRef.h>
#include <wpi/SmallVector.h>

namespace pybind11
{
namespace detail
{

template <typename Type> struct type_caster<wpi::ArrayRef<Type>> {
    using value_conv = make_caster<Type>;
    PYBIND11_TYPE_CASTER(wpi::ArrayRef<Type>, _("List[") + value_conv::name + _("]"));

    wpi::SmallVector<Type, 32> vec;
    bool load(handle src, bool convert) {
        if (!isinstance<sequence>(src) || isinstance<str>(src))
            return false;
        auto s = reinterpret_borrow<sequence>(src);
        vec.reserve(s.size());
        for (auto it : s) {
            value_conv conv;
            if (!conv.load(it, convert))
                return false;
            vec.push_back(cast_op<Type &&>(std::move(conv)));
        }
        value = wpi::ArrayRef<Type>(vec);
        return true;
    }

public:
    template <typename T>
    static handle cast(T &&src, return_value_policy policy, handle parent) {
        if (!std::is_lvalue_reference<T>::value)
            policy = return_value_policy_override<Type>::policy(policy);
        list l(src.size());
        size_t index = 0;
        for (auto &&value : src) {
            auto value_ = reinterpret_steal<object>(value_conv::cast(forward_like<T>(value), policy, parent));
            if (!value_)
                return handle();
            PyList_SET_ITEM(l.ptr(), (ssize_t) index++, value_.release().ptr()); // steals a reference
        }
        return l.release();
    }
};

} // namespace detail
} // namespace pybind11