#pragma once

#include <units/concentration.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::ppm_t> {
  static constexpr auto name = const_name("wpimath.units.parts_per_million");
};

template <> struct unit_type_name<units::parts_per_million> {
  static constexpr auto name = const_name("wpimath.units.parts_per_million");
};

template <> struct unit_type_name<units::ppb_t> {
  static constexpr auto name = const_name("wpimath.units.parts_per_billion");
};

template <> struct unit_type_name<units::parts_per_billion> {
  static constexpr auto name = const_name("wpimath.units.parts_per_billion");
};

template <> struct unit_type_name<units::ppt_t> {
  static constexpr auto name = const_name("wpimath.units.parts_per_trillion");
};

template <> struct unit_type_name<units::parts_per_trillion> {
  static constexpr auto name = const_name("wpimath.units.parts_per_trillion");
};

template <> struct unit_type_name<units::percent_t> {
  static constexpr auto name = const_name("wpimath.units.percent");
};

template <> struct unit_type_name<units::percent> {
  static constexpr auto name = const_name("wpimath.units.percent");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
