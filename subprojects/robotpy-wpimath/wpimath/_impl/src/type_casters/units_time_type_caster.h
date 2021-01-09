#pragma once

#include <units/time.h>

namespace pybind11 {
namespace detail {
template <> struct handle_type_name<units::second_t> {
  static constexpr auto name = _("seconds");
};

template <> struct handle_type_name<units::seconds> {
  static constexpr auto name = _("seconds");
};

template <> struct handle_type_name<units::nanosecond_t> {
  static constexpr auto name = _("nanoseconds");
};

template <> struct handle_type_name<units::nanoseconds> {
  static constexpr auto name = _("nanoseconds");
};

template <> struct handle_type_name<units::microsecond_t> {
  static constexpr auto name = _("microseconds");
};

template <> struct handle_type_name<units::microseconds> {
  static constexpr auto name = _("microseconds");
};

template <> struct handle_type_name<units::millisecond_t> {
  static constexpr auto name = _("milliseconds");
};

template <> struct handle_type_name<units::milliseconds> {
  static constexpr auto name = _("milliseconds");
};

template <> struct handle_type_name<units::kilosecond_t> {
  static constexpr auto name = _("kiloseconds");
};

template <> struct handle_type_name<units::kiloseconds> {
  static constexpr auto name = _("kiloseconds");
};

template <> struct handle_type_name<units::minute_t> {
  static constexpr auto name = _("minutes");
};

template <> struct handle_type_name<units::minutes> {
  static constexpr auto name = _("minutes");
};

template <> struct handle_type_name<units::hour_t> {
  static constexpr auto name = _("hours");
};

template <> struct handle_type_name<units::hours> {
  static constexpr auto name = _("hours");
};

template <> struct handle_type_name<units::day_t> {
  static constexpr auto name = _("days");
};

template <> struct handle_type_name<units::days> {
  static constexpr auto name = _("days");
};

template <> struct handle_type_name<units::week_t> {
  static constexpr auto name = _("weeks");
};

template <> struct handle_type_name<units::weeks> {
  static constexpr auto name = _("weeks");
};

template <> struct handle_type_name<units::year_t> {
  static constexpr auto name = _("years");
};

template <> struct handle_type_name<units::years> {
  static constexpr auto name = _("years");
};

template <> struct handle_type_name<units::julian_year_t> {
  static constexpr auto name = _("julian_years");
};

template <> struct handle_type_name<units::julian_years> {
  static constexpr auto name = _("julian_years");
};

template <> struct handle_type_name<units::gregorian_year_t> {
  static constexpr auto name = _("gregorian_years");
};

template <> struct handle_type_name<units::gregorian_years> {
  static constexpr auto name = _("gregorian_years");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"
