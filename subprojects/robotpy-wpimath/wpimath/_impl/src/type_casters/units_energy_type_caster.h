#pragma once

#include <units/energy.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::joule_t> {
  static constexpr auto name = const_name("wpimath.units.joules");
};

template <> struct unit_type_name<units::joules> {
  static constexpr auto name = const_name("wpimath.units.joules");
};

template <> struct unit_type_name<units::nanojoule_t> {
  static constexpr auto name = const_name("wpimath.units.nanojoules");
};

template <> struct unit_type_name<units::nanojoules> {
  static constexpr auto name = const_name("wpimath.units.nanojoules");
};

template <> struct unit_type_name<units::microjoule_t> {
  static constexpr auto name = const_name("wpimath.units.microjoules");
};

template <> struct unit_type_name<units::microjoules> {
  static constexpr auto name = const_name("wpimath.units.microjoules");
};

template <> struct unit_type_name<units::millijoule_t> {
  static constexpr auto name = const_name("wpimath.units.millijoules");
};

template <> struct unit_type_name<units::millijoules> {
  static constexpr auto name = const_name("wpimath.units.millijoules");
};

template <> struct unit_type_name<units::kilojoule_t> {
  static constexpr auto name = const_name("wpimath.units.kilojoules");
};

template <> struct unit_type_name<units::kilojoules> {
  static constexpr auto name = const_name("wpimath.units.kilojoules");
};

template <> struct unit_type_name<units::calorie_t> {
  static constexpr auto name = const_name("wpimath.units.calories");
};

template <> struct unit_type_name<units::calories> {
  static constexpr auto name = const_name("wpimath.units.calories");
};

template <> struct unit_type_name<units::nanocalorie_t> {
  static constexpr auto name = const_name("wpimath.units.nanocalories");
};

template <> struct unit_type_name<units::nanocalories> {
  static constexpr auto name = const_name("wpimath.units.nanocalories");
};

template <> struct unit_type_name<units::microcalorie_t> {
  static constexpr auto name = const_name("wpimath.units.microcalories");
};

template <> struct unit_type_name<units::microcalories> {
  static constexpr auto name = const_name("wpimath.units.microcalories");
};

template <> struct unit_type_name<units::millicalorie_t> {
  static constexpr auto name = const_name("wpimath.units.millicalories");
};

template <> struct unit_type_name<units::millicalories> {
  static constexpr auto name = const_name("wpimath.units.millicalories");
};

template <> struct unit_type_name<units::kilocalorie_t> {
  static constexpr auto name = const_name("wpimath.units.kilocalories");
};

template <> struct unit_type_name<units::kilocalories> {
  static constexpr auto name = const_name("wpimath.units.kilocalories");
};

template <> struct unit_type_name<units::kilowatt_hour_t> {
  static constexpr auto name = const_name("wpimath.units.kilowatt_hours");
};

template <> struct unit_type_name<units::kilowatt_hours> {
  static constexpr auto name = const_name("wpimath.units.kilowatt_hours");
};

template <> struct unit_type_name<units::watt_hour_t> {
  static constexpr auto name = const_name("wpimath.units.watt_hours");
};

template <> struct unit_type_name<units::watt_hours> {
  static constexpr auto name = const_name("wpimath.units.watt_hours");
};

template <> struct unit_type_name<units::british_thermal_unit_t> {
  static constexpr auto name = const_name("wpimath.units.british_thermal_units");
};

template <> struct unit_type_name<units::british_thermal_units> {
  static constexpr auto name = const_name("wpimath.units.british_thermal_units");
};

template <> struct unit_type_name<units::british_thermal_unit_iso_t> {
  static constexpr auto name = const_name("wpimath.units.british_thermal_units_iso");
};

template <> struct unit_type_name<units::british_thermal_units_iso> {
  static constexpr auto name = const_name("wpimath.units.british_thermal_units_iso");
};

template <> struct unit_type_name<units::british_thermal_unit_59_t> {
  static constexpr auto name = const_name("wpimath.units.british_thermal_units_59");
};

template <> struct unit_type_name<units::british_thermal_units_59> {
  static constexpr auto name = const_name("wpimath.units.british_thermal_units_59");
};

template <> struct unit_type_name<units::therm_t> {
  static constexpr auto name = const_name("wpimath.units.therms");
};

template <> struct unit_type_name<units::therms> {
  static constexpr auto name = const_name("wpimath.units.therms");
};

template <> struct unit_type_name<units::foot_pound_t> {
  static constexpr auto name = const_name("wpimath.units.foot_pounds");
};

template <> struct unit_type_name<units::foot_pounds> {
  static constexpr auto name = const_name("wpimath.units.foot_pounds");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
