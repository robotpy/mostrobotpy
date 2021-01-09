#pragma once

#include <units/solid_angle.h>

namespace pybind11 {
namespace detail {
template <> struct handle_type_name<units::steradian_t> {
  static constexpr auto name = _("steradians");
};

template <> struct handle_type_name<units::steradians> {
  static constexpr auto name = _("steradians");
};

template <> struct handle_type_name<units::nanosteradian_t> {
  static constexpr auto name = _("nanosteradians");
};

template <> struct handle_type_name<units::nanosteradians> {
  static constexpr auto name = _("nanosteradians");
};

template <> struct handle_type_name<units::microsteradian_t> {
  static constexpr auto name = _("microsteradians");
};

template <> struct handle_type_name<units::microsteradians> {
  static constexpr auto name = _("microsteradians");
};

template <> struct handle_type_name<units::millisteradian_t> {
  static constexpr auto name = _("millisteradians");
};

template <> struct handle_type_name<units::millisteradians> {
  static constexpr auto name = _("millisteradians");
};

template <> struct handle_type_name<units::kilosteradian_t> {
  static constexpr auto name = _("kilosteradians");
};

template <> struct handle_type_name<units::kilosteradians> {
  static constexpr auto name = _("kilosteradians");
};

template <> struct handle_type_name<units::degree_squared_t> {
  static constexpr auto name = _("degrees_squared");
};

template <> struct handle_type_name<units::degrees_squared> {
  static constexpr auto name = _("degrees_squared");
};

template <> struct handle_type_name<units::spat_t> {
  static constexpr auto name = _("spats");
};

template <> struct handle_type_name<units::spats> {
  static constexpr auto name = _("spats");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"
