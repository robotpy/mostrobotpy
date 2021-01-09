#pragma once

#include <units/velocity.h>

namespace pybind11 {
namespace detail {
template <> struct handle_type_name<units::meters_per_second_t> {
  static constexpr auto name = _("meters_per_second");
};

template <> struct handle_type_name<units::meters_per_second> {
  static constexpr auto name = _("meters_per_second");
};

template <> struct handle_type_name<units::feet_per_second_t> {
  static constexpr auto name = _("feet_per_second");
};

template <> struct handle_type_name<units::feet_per_second> {
  static constexpr auto name = _("feet_per_second");
};

template <> struct handle_type_name<units::miles_per_hour_t> {
  static constexpr auto name = _("miles_per_hour");
};

template <> struct handle_type_name<units::miles_per_hour> {
  static constexpr auto name = _("miles_per_hour");
};

template <> struct handle_type_name<units::kilometers_per_hour_t> {
  static constexpr auto name = _("kilometers_per_hour");
};

template <> struct handle_type_name<units::kilometers_per_hour> {
  static constexpr auto name = _("kilometers_per_hour");
};

template <> struct handle_type_name<units::knot_t> {
  static constexpr auto name = _("knots");
};

template <> struct handle_type_name<units::knots> {
  static constexpr auto name = _("knots");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"
