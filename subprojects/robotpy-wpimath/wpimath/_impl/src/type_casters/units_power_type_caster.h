#pragma once

#include <units/power.h>

namespace pybind11 {
namespace detail {
template <> struct handle_type_name<units::watt_t> {
  static constexpr auto name = _("watts");
};

template <> struct handle_type_name<units::watts> {
  static constexpr auto name = _("watts");
};

template <> struct handle_type_name<units::nanowatt_t> {
  static constexpr auto name = _("nanowatts");
};

template <> struct handle_type_name<units::nanowatts> {
  static constexpr auto name = _("nanowatts");
};

template <> struct handle_type_name<units::microwatt_t> {
  static constexpr auto name = _("microwatts");
};

template <> struct handle_type_name<units::microwatts> {
  static constexpr auto name = _("microwatts");
};

template <> struct handle_type_name<units::milliwatt_t> {
  static constexpr auto name = _("milliwatts");
};

template <> struct handle_type_name<units::milliwatts> {
  static constexpr auto name = _("milliwatts");
};

template <> struct handle_type_name<units::kilowatt_t> {
  static constexpr auto name = _("kilowatts");
};

template <> struct handle_type_name<units::kilowatts> {
  static constexpr auto name = _("kilowatts");
};

template <> struct handle_type_name<units::horsepower_t> {
  static constexpr auto name = _("horsepower");
};

template <> struct handle_type_name<units::horsepower> {
  static constexpr auto name = _("horsepower");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"
