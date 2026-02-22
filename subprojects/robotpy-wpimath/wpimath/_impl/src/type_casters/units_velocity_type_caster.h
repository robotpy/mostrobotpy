#pragma once

#include <units/velocity.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::meters_per_second_t> {
  static constexpr auto name = const_name("wpimath.units.meters_per_second");
};

template <> struct unit_type_name<units::meters_per_second> {
  static constexpr auto name = const_name("wpimath.units.meters_per_second");
};

template <> struct unit_type_name<units::feet_per_second_t> {
  static constexpr auto name = const_name("wpimath.units.feet_per_second");
};

template <> struct unit_type_name<units::feet_per_second> {
  static constexpr auto name = const_name("wpimath.units.feet_per_second");
};

template <> struct unit_type_name<units::miles_per_hour_t> {
  static constexpr auto name = const_name("wpimath.units.miles_per_hour");
};

template <> struct unit_type_name<units::miles_per_hour> {
  static constexpr auto name = const_name("wpimath.units.miles_per_hour");
};

template <> struct unit_type_name<units::kilometers_per_hour_t> {
  static constexpr auto name = const_name("wpimath.units.kilometers_per_hour");
};

template <> struct unit_type_name<units::kilometers_per_hour> {
  static constexpr auto name = const_name("wpimath.units.kilometers_per_hour");
};

template <> struct unit_type_name<units::knot_t> {
  static constexpr auto name = const_name("wpimath.units.knots");
};

template <> struct unit_type_name<units::knots> {
  static constexpr auto name = const_name("wpimath.units.knots");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
