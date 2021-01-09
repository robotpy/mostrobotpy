#pragma once

#include <units/angle.h>
#include <units/angular_velocity.h>
#include <units/length.h>
#include <units/time.h>
#include <units/voltage.h>

namespace pybind11 {
namespace detail {

template <>
struct handle_type_name<units::unit_t<
    units::compound_unit<units::radian, units::inverse<units::meter>>>> {
  static constexpr auto name = _("radians_per_meter");
};

template <>
struct handle_type_name<units::unit_t<units::compound_unit<
    units::radians_per_second, units::inverse<units::seconds>>>> {
  static constexpr auto name = _("radians_per_second_squared");
};

template <>
struct handle_type_name<units::unit_t<units::inverse<units::seconds>>> {
  static constexpr auto name = _("units_per_second");
};

template <>
struct handle_type_name<
    units::unit_t<units::inverse<units::squared<units::seconds>>>> {
  static constexpr auto name = _("units_per_second_squared");
};

using volt_seconds = units::compound_unit<units::volts, units::seconds>;
using volt_seconds_squared = units::compound_unit<volt_seconds, units::seconds>;

template <> struct handle_type_name<units::unit_t<volt_seconds>> {
  static constexpr auto name = _("volt_seconds");
};

template <> struct handle_type_name<units::unit_t<volt_seconds_squared>> {
  static constexpr auto name = _("volt_seconds_squared");
};

template <>
struct handle_type_name<units::unit_t<
    units::compound_unit<volt_seconds, units::inverse<units::meter>>>> {
  static constexpr auto name = _("volt_seconds_per_meter");
};
template <>
struct handle_type_name<units::unit_t<
    units::compound_unit<volt_seconds_squared, units::inverse<units::meter>>>> {
  static constexpr auto name = _("volt_seconds_squared_per_meter");
};
template <>
struct handle_type_name<units::unit_t<
    units::compound_unit<volt_seconds, units::inverse<units::feet>>>> {
  static constexpr auto name = _("volt_seconds_per_feet");
};
template <>
struct handle_type_name<units::unit_t<
    units::compound_unit<volt_seconds_squared, units::inverse<units::feet>>>> {
  static constexpr auto name = _("volt_seconds_squared_per_feet");
};
template <>
struct handle_type_name<units::unit_t<
    units::compound_unit<volt_seconds, units::inverse<units::radian>>>> {
  static constexpr auto name = _("volt_seconds_per_radian");
};
template <>
struct handle_type_name<units::unit_t<units::compound_unit<
    volt_seconds_squared, units::inverse<units::radian>>>> {
  static constexpr auto name = _("volt_seconds_squared_per_radian");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"