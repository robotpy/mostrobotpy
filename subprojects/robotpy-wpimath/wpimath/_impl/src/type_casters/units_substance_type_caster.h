#pragma once

#include <units/substance.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::mole_t> {
  static constexpr auto name = const_name("wpimath.units.moles");
};

template <> struct unit_type_name<units::moles> {
  static constexpr auto name = const_name("wpimath.units.moles");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
