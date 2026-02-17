
#pragma once

#include <nanobind/nanobind.h>

#include "wpi_smallvector_type_caster.h"

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename Type> struct type_caster<wpi::SmallVectorImpl<Type>> {

    using Value = wpi::SmallVectorImpl<Type>;
    using Caster = make_caster<Type>;
    using VecCaster = make_caster<wpi::SmallVector<Type, 16>>;

    /// This caster constructs instances on the fly. Because of this, only the
    /// `operator Value()` cast operator is implemented below, and the type
    /// alias below informs users of this class of this fact.
    template <typename T> using Cast = Value&;

    static constexpr auto Name = VecCaster::Name; 
  
    // Can't use NB_TYPE_CASTER because SmallVectorImpl is not default constructable
    VecCaster caster;

    bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept {
        return caster.from_python(src, flags, cleanup);
    }

    explicit operator Value&() {
        return caster.value;
    }

    template <typename T>
    static handle from_cpp(T *value, rv_policy policy, cleanup_list *cleanup) {
        if (!value)
            return none().release();
        return from_cpp(*value, policy, cleanup);
    }

    template <typename T>
    static handle from_cpp(T &&src, rv_policy policy, cleanup_list *cleanup) noexcept {
        return VecCaster::from_cpp(src, policy, cleanup);
    }

    template <typename T>
    bool can_cast() const noexcept {
        return true;
    }    
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)
