#pragma once

#include <units/energy.h>

namespace pybind11 {
namespace detail {
template <> struct handle_type_name<units::joule_t> {
  static constexpr auto name = _("joules");
};

template <> struct handle_type_name<units::joules> {
  static constexpr auto name = _("joules");
};

template <> struct handle_type_name<units::nanojoule_t> {
  static constexpr auto name = _("nanojoules");
};

template <> struct handle_type_name<units::nanojoules> {
  static constexpr auto name = _("nanojoules");
};

template <> struct handle_type_name<units::microjoule_t> {
  static constexpr auto name = _("microjoules");
};

template <> struct handle_type_name<units::microjoules> {
  static constexpr auto name = _("microjoules");
};

template <> struct handle_type_name<units::millijoule_t> {
  static constexpr auto name = _("millijoules");
};

template <> struct handle_type_name<units::millijoules> {
  static constexpr auto name = _("millijoules");
};

template <> struct handle_type_name<units::kilojoule_t> {
  static constexpr auto name = _("kilojoules");
};

template <> struct handle_type_name<units::kilojoules> {
  static constexpr auto name = _("kilojoules");
};

template <> struct handle_type_name<units::calorie_t> {
  static constexpr auto name = _("calories");
};

template <> struct handle_type_name<units::calories> {
  static constexpr auto name = _("calories");
};

template <> struct handle_type_name<units::nanocalorie_t> {
  static constexpr auto name = _("nanocalories");
};

template <> struct handle_type_name<units::nanocalories> {
  static constexpr auto name = _("nanocalories");
};

template <> struct handle_type_name<units::microcalorie_t> {
  static constexpr auto name = _("microcalories");
};

template <> struct handle_type_name<units::microcalories> {
  static constexpr auto name = _("microcalories");
};

template <> struct handle_type_name<units::millicalorie_t> {
  static constexpr auto name = _("millicalories");
};

template <> struct handle_type_name<units::millicalories> {
  static constexpr auto name = _("millicalories");
};

template <> struct handle_type_name<units::kilocalorie_t> {
  static constexpr auto name = _("kilocalories");
};

template <> struct handle_type_name<units::kilocalories> {
  static constexpr auto name = _("kilocalories");
};

template <> struct handle_type_name<units::kilowatt_hour_t> {
  static constexpr auto name = _("kilowatt_hours");
};

template <> struct handle_type_name<units::kilowatt_hours> {
  static constexpr auto name = _("kilowatt_hours");
};

template <> struct handle_type_name<units::watt_hour_t> {
  static constexpr auto name = _("watt_hours");
};

template <> struct handle_type_name<units::watt_hours> {
  static constexpr auto name = _("watt_hours");
};

template <> struct handle_type_name<units::british_thermal_unit_t> {
  static constexpr auto name = _("british_thermal_units");
};

template <> struct handle_type_name<units::british_thermal_units> {
  static constexpr auto name = _("british_thermal_units");
};

template <> struct handle_type_name<units::british_thermal_unit_iso_t> {
  static constexpr auto name = _("british_thermal_units_iso");
};

template <> struct handle_type_name<units::british_thermal_units_iso> {
  static constexpr auto name = _("british_thermal_units_iso");
};

template <> struct handle_type_name<units::british_thermal_unit_59_t> {
  static constexpr auto name = _("british_thermal_units_59");
};

template <> struct handle_type_name<units::british_thermal_units_59> {
  static constexpr auto name = _("british_thermal_units_59");
};

template <> struct handle_type_name<units::therm_t> {
  static constexpr auto name = _("therms");
};

template <> struct handle_type_name<units::therms> {
  static constexpr auto name = _("therms");
};

template <> struct handle_type_name<units::foot_pound_t> {
  static constexpr auto name = _("foot_pounds");
};

template <> struct handle_type_name<units::foot_pounds> {
  static constexpr auto name = _("foot_pounds");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"
