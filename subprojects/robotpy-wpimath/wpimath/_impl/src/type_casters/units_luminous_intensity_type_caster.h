#pragma once

#include <units/luminous_intensity.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::candela_t> {
  static constexpr auto name = const_name("wpimath.units.candelas");
};

template <> struct unit_type_name<units::candelas> {
  static constexpr auto name = const_name("wpimath.units.candelas");
};

template <> struct unit_type_name<units::nanocandela_t> {
  static constexpr auto name = const_name("wpimath.units.nanocandelas");
};

template <> struct unit_type_name<units::nanocandelas> {
  static constexpr auto name = const_name("wpimath.units.nanocandelas");
};

template <> struct unit_type_name<units::microcandela_t> {
  static constexpr auto name = const_name("wpimath.units.microcandelas");
};

template <> struct unit_type_name<units::microcandelas> {
  static constexpr auto name = const_name("wpimath.units.microcandelas");
};

template <> struct unit_type_name<units::millicandela_t> {
  static constexpr auto name = const_name("wpimath.units.millicandelas");
};

template <> struct unit_type_name<units::millicandelas> {
  static constexpr auto name = const_name("wpimath.units.millicandelas");
};

template <> struct unit_type_name<units::kilocandela_t> {
  static constexpr auto name = const_name("wpimath.units.kilocandelas");
};

template <> struct unit_type_name<units::kilocandelas> {
  static constexpr auto name = const_name("wpimath.units.kilocandelas");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
