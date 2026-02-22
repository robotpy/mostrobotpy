#pragma once

#include <units/temperature.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::kelvin_t> {
  static constexpr auto name = const_name("wpimath.units.kelvin");
};

template <> struct unit_type_name<units::kelvin> {
  static constexpr auto name = const_name("wpimath.units.kelvin");
};

template <> struct unit_type_name<units::celsius_t> {
  static constexpr auto name = const_name("wpimath.units.celsius");
};

template <> struct unit_type_name<units::celsius> {
  static constexpr auto name = const_name("wpimath.units.celsius");
};

template <> struct unit_type_name<units::fahrenheit_t> {
  static constexpr auto name = const_name("wpimath.units.fahrenheit");
};

template <> struct unit_type_name<units::fahrenheit> {
  static constexpr auto name = const_name("wpimath.units.fahrenheit");
};

template <> struct unit_type_name<units::reaumur_t> {
  static constexpr auto name = const_name("wpimath.units.reaumur");
};

template <> struct unit_type_name<units::reaumur> {
  static constexpr auto name = const_name("wpimath.units.reaumur");
};

template <> struct unit_type_name<units::rankine_t> {
  static constexpr auto name = const_name("wpimath.units.rankine");
};

template <> struct unit_type_name<units::rankine> {
  static constexpr auto name = const_name("wpimath.units.rankine");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
