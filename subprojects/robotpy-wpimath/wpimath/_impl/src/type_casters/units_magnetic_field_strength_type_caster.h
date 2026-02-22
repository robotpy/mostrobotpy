#pragma once

#include <units/magnetic_field_strength.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::tesla_t> {
  static constexpr auto name = const_name("wpimath.units.teslas");
};

template <> struct unit_type_name<units::teslas> {
  static constexpr auto name = const_name("wpimath.units.teslas");
};

template <> struct unit_type_name<units::nanotesla_t> {
  static constexpr auto name = const_name("wpimath.units.nanoteslas");
};

template <> struct unit_type_name<units::nanoteslas> {
  static constexpr auto name = const_name("wpimath.units.nanoteslas");
};

template <> struct unit_type_name<units::microtesla_t> {
  static constexpr auto name = const_name("wpimath.units.microteslas");
};

template <> struct unit_type_name<units::microteslas> {
  static constexpr auto name = const_name("wpimath.units.microteslas");
};

template <> struct unit_type_name<units::millitesla_t> {
  static constexpr auto name = const_name("wpimath.units.milliteslas");
};

template <> struct unit_type_name<units::milliteslas> {
  static constexpr auto name = const_name("wpimath.units.milliteslas");
};

template <> struct unit_type_name<units::kilotesla_t> {
  static constexpr auto name = const_name("wpimath.units.kiloteslas");
};

template <> struct unit_type_name<units::kiloteslas> {
  static constexpr auto name = const_name("wpimath.units.kiloteslas");
};

template <> struct unit_type_name<units::gauss_t> {
  static constexpr auto name = const_name("wpimath.units.gauss");
};

template <> struct unit_type_name<units::gauss> {
  static constexpr auto name = const_name("wpimath.units.gauss");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
