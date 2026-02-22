#pragma once

#include <units/solid_angle.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::steradian_t> {
  static constexpr auto name = const_name("wpimath.units.steradians");
};

template <> struct unit_type_name<units::steradians> {
  static constexpr auto name = const_name("wpimath.units.steradians");
};

template <> struct unit_type_name<units::nanosteradian_t> {
  static constexpr auto name = const_name("wpimath.units.nanosteradians");
};

template <> struct unit_type_name<units::nanosteradians> {
  static constexpr auto name = const_name("wpimath.units.nanosteradians");
};

template <> struct unit_type_name<units::microsteradian_t> {
  static constexpr auto name = const_name("wpimath.units.microsteradians");
};

template <> struct unit_type_name<units::microsteradians> {
  static constexpr auto name = const_name("wpimath.units.microsteradians");
};

template <> struct unit_type_name<units::millisteradian_t> {
  static constexpr auto name = const_name("wpimath.units.millisteradians");
};

template <> struct unit_type_name<units::millisteradians> {
  static constexpr auto name = const_name("wpimath.units.millisteradians");
};

template <> struct unit_type_name<units::kilosteradian_t> {
  static constexpr auto name = const_name("wpimath.units.kilosteradians");
};

template <> struct unit_type_name<units::kilosteradians> {
  static constexpr auto name = const_name("wpimath.units.kilosteradians");
};

template <> struct unit_type_name<units::degree_squared_t> {
  static constexpr auto name = const_name("wpimath.units.degrees_squared");
};

template <> struct unit_type_name<units::degrees_squared> {
  static constexpr auto name = const_name("wpimath.units.degrees_squared");
};

template <> struct unit_type_name<units::spat_t> {
  static constexpr auto name = const_name("wpimath.units.spats");
};

template <> struct unit_type_name<units::spats> {
  static constexpr auto name = const_name("wpimath.units.spats");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
