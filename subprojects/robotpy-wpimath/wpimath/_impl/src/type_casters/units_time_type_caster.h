#pragma once

#include <units/time.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::second_t> {
  static constexpr auto name = const_name("wpimath.units.seconds");
};

template <> struct unit_type_name<units::seconds> {
  static constexpr auto name = const_name("wpimath.units.seconds");
};

template <> struct unit_type_name<units::nanosecond_t> {
  static constexpr auto name = const_name("wpimath.units.nanoseconds");
};

template <> struct unit_type_name<units::nanoseconds> {
  static constexpr auto name = const_name("wpimath.units.nanoseconds");
};

template <> struct unit_type_name<units::microsecond_t> {
  static constexpr auto name = const_name("wpimath.units.microseconds");
};

template <> struct unit_type_name<units::microseconds> {
  static constexpr auto name = const_name("wpimath.units.microseconds");
};

template <> struct unit_type_name<units::millisecond_t> {
  static constexpr auto name = const_name("wpimath.units.milliseconds");
};

template <> struct unit_type_name<units::milliseconds> {
  static constexpr auto name = const_name("wpimath.units.milliseconds");
};

template <> struct unit_type_name<units::kilosecond_t> {
  static constexpr auto name = const_name("wpimath.units.kiloseconds");
};

template <> struct unit_type_name<units::kiloseconds> {
  static constexpr auto name = const_name("wpimath.units.kiloseconds");
};

template <> struct unit_type_name<units::minute_t> {
  static constexpr auto name = const_name("wpimath.units.minutes");
};

template <> struct unit_type_name<units::minutes> {
  static constexpr auto name = const_name("wpimath.units.minutes");
};

template <> struct unit_type_name<units::hour_t> {
  static constexpr auto name = const_name("wpimath.units.hours");
};

template <> struct unit_type_name<units::hours> {
  static constexpr auto name = const_name("wpimath.units.hours");
};

template <> struct unit_type_name<units::day_t> {
  static constexpr auto name = const_name("wpimath.units.days");
};

template <> struct unit_type_name<units::days> {
  static constexpr auto name = const_name("wpimath.units.days");
};

template <> struct unit_type_name<units::week_t> {
  static constexpr auto name = const_name("wpimath.units.weeks");
};

template <> struct unit_type_name<units::weeks> {
  static constexpr auto name = const_name("wpimath.units.weeks");
};

template <> struct unit_type_name<units::year_t> {
  static constexpr auto name = const_name("wpimath.units.years");
};

template <> struct unit_type_name<units::years> {
  static constexpr auto name = const_name("wpimath.units.years");
};

template <> struct unit_type_name<units::julian_year_t> {
  static constexpr auto name = const_name("wpimath.units.julian_years");
};

template <> struct unit_type_name<units::julian_years> {
  static constexpr auto name = const_name("wpimath.units.julian_years");
};

template <> struct unit_type_name<units::gregorian_year_t> {
  static constexpr auto name = const_name("wpimath.units.gregorian_years");
};

template <> struct unit_type_name<units::gregorian_years> {
  static constexpr auto name = const_name("wpimath.units.gregorian_years");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
