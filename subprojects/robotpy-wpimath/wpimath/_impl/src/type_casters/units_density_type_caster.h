#pragma once

#include <units/density.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::kilograms_per_cubic_meter_t> {
  static constexpr auto name = const_name("wpimath.units.kilograms_per_cubic_meter");
};

template <> struct unit_type_name<units::kilograms_per_cubic_meter> {
  static constexpr auto name = const_name("wpimath.units.kilograms_per_cubic_meter");
};

template <> struct unit_type_name<units::grams_per_milliliter_t> {
  static constexpr auto name = const_name("wpimath.units.grams_per_milliliter");
};

template <> struct unit_type_name<units::grams_per_milliliter> {
  static constexpr auto name = const_name("wpimath.units.grams_per_milliliter");
};

template <> struct unit_type_name<units::kilograms_per_liter_t> {
  static constexpr auto name = const_name("wpimath.units.kilograms_per_liter");
};

template <> struct unit_type_name<units::kilograms_per_liter> {
  static constexpr auto name = const_name("wpimath.units.kilograms_per_liter");
};

template <> struct unit_type_name<units::ounces_per_cubic_foot_t> {
  static constexpr auto name = const_name("wpimath.units.ounces_per_cubic_foot");
};

template <> struct unit_type_name<units::ounces_per_cubic_foot> {
  static constexpr auto name = const_name("wpimath.units.ounces_per_cubic_foot");
};

template <> struct unit_type_name<units::ounces_per_cubic_inch_t> {
  static constexpr auto name = const_name("wpimath.units.ounces_per_cubic_inch");
};

template <> struct unit_type_name<units::ounces_per_cubic_inch> {
  static constexpr auto name = const_name("wpimath.units.ounces_per_cubic_inch");
};

template <> struct unit_type_name<units::ounces_per_gallon_t> {
  static constexpr auto name = const_name("wpimath.units.ounces_per_gallon");
};

template <> struct unit_type_name<units::ounces_per_gallon> {
  static constexpr auto name = const_name("wpimath.units.ounces_per_gallon");
};

template <> struct unit_type_name<units::pounds_per_cubic_foot_t> {
  static constexpr auto name = const_name("wpimath.units.pounds_per_cubic_foot");
};

template <> struct unit_type_name<units::pounds_per_cubic_foot> {
  static constexpr auto name = const_name("wpimath.units.pounds_per_cubic_foot");
};

template <> struct unit_type_name<units::pounds_per_cubic_inch_t> {
  static constexpr auto name = const_name("wpimath.units.pounds_per_cubic_inch");
};

template <> struct unit_type_name<units::pounds_per_cubic_inch> {
  static constexpr auto name = const_name("wpimath.units.pounds_per_cubic_inch");
};

template <> struct unit_type_name<units::pounds_per_gallon_t> {
  static constexpr auto name = const_name("wpimath.units.pounds_per_gallon");
};

template <> struct unit_type_name<units::pounds_per_gallon> {
  static constexpr auto name = const_name("wpimath.units.pounds_per_gallon");
};

template <> struct unit_type_name<units::slugs_per_cubic_foot_t> {
  static constexpr auto name = const_name("wpimath.units.slugs_per_cubic_foot");
};

template <> struct unit_type_name<units::slugs_per_cubic_foot> {
  static constexpr auto name = const_name("wpimath.units.slugs_per_cubic_foot");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
