#pragma once

#include <units/acceleration.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::meters_per_second_squared_t> {
  static constexpr auto name = const_name("wpimath.units.meters_per_second_squared");
};

template <> struct unit_type_name<units::meters_per_second_squared> {
  static constexpr auto name = const_name("wpimath.units.meters_per_second_squared");
};

template <> struct unit_type_name<units::feet_per_second_squared_t> {
  static constexpr auto name = const_name("wpimath.units.feet_per_second_squared");
};

template <> struct unit_type_name<units::feet_per_second_squared> {
  static constexpr auto name = const_name("wpimath.units.feet_per_second_squared");
};

template <> struct unit_type_name<units::standard_gravity_t> {
  static constexpr auto name = const_name("wpimath.units.standard_gravity");
};

template <> struct unit_type_name<units::standard_gravity> {
  static constexpr auto name = const_name("wpimath.units.standard_gravity");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
