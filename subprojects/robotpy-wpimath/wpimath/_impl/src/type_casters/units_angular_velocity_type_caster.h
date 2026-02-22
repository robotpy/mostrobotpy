#pragma once

#include <units/angular_velocity.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::radians_per_second_t> {
  static constexpr auto name = const_name("wpimath.units.radians_per_second");
};

template <> struct unit_type_name<units::radians_per_second> {
  static constexpr auto name = const_name("wpimath.units.radians_per_second");
};

template <> struct unit_type_name<units::degrees_per_second_t> {
  static constexpr auto name = const_name("wpimath.units.degrees_per_second");
};

template <> struct unit_type_name<units::degrees_per_second> {
  static constexpr auto name = const_name("wpimath.units.degrees_per_second");
};

template <> struct unit_type_name<units::turns_per_second_t> {
  static constexpr auto name = const_name("wpimath.units.turns_per_second");
};

template <> struct unit_type_name<units::turns_per_second> {
  static constexpr auto name = const_name("wpimath.units.turns_per_second");
};

template <> struct unit_type_name<units::revolutions_per_minute_t> {
  static constexpr auto name = const_name("wpimath.units.revolutions_per_minute");
};

template <> struct unit_type_name<units::revolutions_per_minute> {
  static constexpr auto name = const_name("wpimath.units.revolutions_per_minute");
};

template <> struct unit_type_name<units::milliarcseconds_per_year_t> {
  static constexpr auto name = const_name("wpimath.units.milliarcseconds_per_year");
};

template <> struct unit_type_name<units::milliarcseconds_per_year> {
  static constexpr auto name = const_name("wpimath.units.milliarcseconds_per_year");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
