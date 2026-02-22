#pragma once

#include <units/angular_acceleration.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::radians_per_second_squared_t> {
  static constexpr auto name = const_name("wpimath.units.radians_per_second_squared");
};

template <> struct unit_type_name<units::radians_per_second_squared> {
  static constexpr auto name = const_name("wpimath.units.radians_per_second_squared");
};

template <> struct unit_type_name<units::degrees_per_second_squared_t> {
  static constexpr auto name = const_name("wpimath.units.degrees_per_second_squared");
};

template <> struct unit_type_name<units::degrees_per_second_squared> {
  static constexpr auto name = const_name("wpimath.units.degrees_per_second_squared");
};

template <> struct unit_type_name<units::turns_per_second_squared_t> {
  static constexpr auto name = const_name("wpimath.units.turns_per_second_squared");
};

template <> struct unit_type_name<units::turns_per_second_squared> {
  static constexpr auto name = const_name("wpimath.units.turns_per_second_squared");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
