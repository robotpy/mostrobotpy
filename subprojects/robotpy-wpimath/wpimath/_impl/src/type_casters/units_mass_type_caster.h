#pragma once

#include <units/mass.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::gram_t> {
  static constexpr auto name = const_name("wpimath.units.grams");
};

template <> struct unit_type_name<units::grams> {
  static constexpr auto name = const_name("wpimath.units.grams");
};

template <> struct unit_type_name<units::nanogram_t> {
  static constexpr auto name = const_name("wpimath.units.nanograms");
};

template <> struct unit_type_name<units::nanograms> {
  static constexpr auto name = const_name("wpimath.units.nanograms");
};

template <> struct unit_type_name<units::microgram_t> {
  static constexpr auto name = const_name("wpimath.units.micrograms");
};

template <> struct unit_type_name<units::micrograms> {
  static constexpr auto name = const_name("wpimath.units.micrograms");
};

template <> struct unit_type_name<units::milligram_t> {
  static constexpr auto name = const_name("wpimath.units.milligrams");
};

template <> struct unit_type_name<units::milligrams> {
  static constexpr auto name = const_name("wpimath.units.milligrams");
};

template <> struct unit_type_name<units::kilogram_t> {
  static constexpr auto name = const_name("wpimath.units.kilograms");
};

template <> struct unit_type_name<units::kilograms> {
  static constexpr auto name = const_name("wpimath.units.kilograms");
};

template <> struct unit_type_name<units::metric_ton_t> {
  static constexpr auto name = const_name("wpimath.units.metric_tons");
};

template <> struct unit_type_name<units::metric_tons> {
  static constexpr auto name = const_name("wpimath.units.metric_tons");
};

template <> struct unit_type_name<units::pound_t> {
  static constexpr auto name = const_name("wpimath.units.pounds");
};

template <> struct unit_type_name<units::pounds> {
  static constexpr auto name = const_name("wpimath.units.pounds");
};

template <> struct unit_type_name<units::long_ton_t> {
  static constexpr auto name = const_name("wpimath.units.long_tons");
};

template <> struct unit_type_name<units::long_tons> {
  static constexpr auto name = const_name("wpimath.units.long_tons");
};

template <> struct unit_type_name<units::short_ton_t> {
  static constexpr auto name = const_name("wpimath.units.short_tons");
};

template <> struct unit_type_name<units::short_tons> {
  static constexpr auto name = const_name("wpimath.units.short_tons");
};

template <> struct unit_type_name<units::stone_t> {
  static constexpr auto name = const_name("wpimath.units.stone");
};

template <> struct unit_type_name<units::stone> {
  static constexpr auto name = const_name("wpimath.units.stone");
};

template <> struct unit_type_name<units::ounce_t> {
  static constexpr auto name = const_name("wpimath.units.ounces");
};

template <> struct unit_type_name<units::ounces> {
  static constexpr auto name = const_name("wpimath.units.ounces");
};

template <> struct unit_type_name<units::carat_t> {
  static constexpr auto name = const_name("wpimath.units.carats");
};

template <> struct unit_type_name<units::carats> {
  static constexpr auto name = const_name("wpimath.units.carats");
};

template <> struct unit_type_name<units::slug_t> {
  static constexpr auto name = const_name("wpimath.units.slugs");
};

template <> struct unit_type_name<units::slugs> {
  static constexpr auto name = const_name("wpimath.units.slugs");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
