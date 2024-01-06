
#pragma once

#include <pybind11/pybind11.h>

#include <wpi/StringMap.h>

namespace pybind11
{
namespace detail
{


template <typename Value>
struct type_caster<wpi::StringMap<Value>> {
    using Type = wpi::StringMap<Value>;
    using Key = std::string_view;
    
    using key_conv = make_caster<Key>;
    using value_conv = make_caster<Value>;

    bool load(handle src, bool convert) {
        if (!isinstance<dict>(src)) {
            return false;
        }
        auto d = reinterpret_borrow<dict>(src);
        value.clear();
        for (auto it : d) {
            key_conv kconv;
            value_conv vconv;
            if (!kconv.load(it.first.ptr(), convert) || !vconv.load(it.second.ptr(), convert)) {
                return false;
            }
            // this is different from pybind11/stl.h map_caster
            value.try_emplace(cast_op<Key &&>(std::move(kconv)), cast_op<Value &&>(std::move(vconv)));
        }
        return true;
    }

    template <typename T>
    static handle cast(T &&src, return_value_policy policy, handle parent) {
        dict d;
        return_value_policy policy_key = policy;
        return_value_policy policy_value = policy;
        if (!std::is_lvalue_reference<T>::value) {
            policy_key = return_value_policy_override<Key>::policy(policy_key);
            policy_value = return_value_policy_override<Value>::policy(policy_value);
        }
        for (auto &&kv : src) {
            // getKey/getValue is different from pybind11/stl.h map_caster
            auto key = reinterpret_steal<object>(
                key_conv::cast(forward_like<T>(kv.getKey()), policy_key, parent));
            auto value = reinterpret_steal<object>(
                value_conv::cast(forward_like<T>(kv.getValue()), policy_value, parent));
            if (!key || !value) {
                return handle();
            }
            d[std::move(key)] = std::move(value);
        }
        return d.release();
    }

    PYBIND11_TYPE_CASTER(Type,
                         const_name("Dict[") + key_conv::name + const_name(", ") + value_conv::name
                             + const_name("]"));
};

} // namespace detail
} // namespace pybind11