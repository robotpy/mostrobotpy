#pragma once

#include <units/area.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::square_meter_t> {
  static constexpr auto name = const_name("wpimath.units.square_meters");
};

template <> struct unit_type_name<units::square_meters> {
  static constexpr auto name = const_name("wpimath.units.square_meters");
};

template <> struct unit_type_name<units::square_foot_t> {
  static constexpr auto name = const_name("wpimath.units.square_feet");
};

template <> struct unit_type_name<units::square_feet> {
  static constexpr auto name = const_name("wpimath.units.square_feet");
};

template <> struct unit_type_name<units::square_inch_t> {
  static constexpr auto name = const_name("wpimath.units.square_inches");
};

template <> struct unit_type_name<units::square_inches> {
  static constexpr auto name = const_name("wpimath.units.square_inches");
};

template <> struct unit_type_name<units::square_mile_t> {
  static constexpr auto name = const_name("wpimath.units.square_miles");
};

template <> struct unit_type_name<units::square_miles> {
  static constexpr auto name = const_name("wpimath.units.square_miles");
};

template <> struct unit_type_name<units::square_kilometer_t> {
  static constexpr auto name = const_name("wpimath.units.square_kilometers");
};

template <> struct unit_type_name<units::square_kilometers> {
  static constexpr auto name = const_name("wpimath.units.square_kilometers");
};

template <> struct unit_type_name<units::hectare_t> {
  static constexpr auto name = const_name("wpimath.units.hectares");
};

template <> struct unit_type_name<units::hectares> {
  static constexpr auto name = const_name("wpimath.units.hectares");
};

template <> struct unit_type_name<units::acre_t> {
  static constexpr auto name = const_name("wpimath.units.acres");
};

template <> struct unit_type_name<units::acres> {
  static constexpr auto name = const_name("wpimath.units.acres");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
