#pragma once

#include <units/angular_velocity.h>

namespace pybind11 {
namespace detail {
template <> struct handle_type_name<units::radians_per_second_t> {
  static constexpr auto name = _("radians_per_second");
};

template <> struct handle_type_name<units::radians_per_second> {
  static constexpr auto name = _("radians_per_second");
};

template <> struct handle_type_name<units::degrees_per_second_t> {
  static constexpr auto name = _("degrees_per_second");
};

template <> struct handle_type_name<units::degrees_per_second> {
  static constexpr auto name = _("degrees_per_second");
};

template <> struct handle_type_name<units::revolutions_per_minute_t> {
  static constexpr auto name = _("revolutions_per_minute");
};

template <> struct handle_type_name<units::revolutions_per_minute> {
  static constexpr auto name = _("revolutions_per_minute");
};

template <> struct handle_type_name<units::milliarcseconds_per_year_t> {
  static constexpr auto name = _("milliarcseconds_per_year");
};

template <> struct handle_type_name<units::milliarcseconds_per_year> {
  static constexpr auto name = _("milliarcseconds_per_year");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"
