#pragma once

#include <units/power.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::watt_t> {
  static constexpr auto name = const_name("wpimath.units.watts");
};

template <> struct unit_type_name<units::watts> {
  static constexpr auto name = const_name("wpimath.units.watts");
};

template <> struct unit_type_name<units::nanowatt_t> {
  static constexpr auto name = const_name("wpimath.units.nanowatts");
};

template <> struct unit_type_name<units::nanowatts> {
  static constexpr auto name = const_name("wpimath.units.nanowatts");
};

template <> struct unit_type_name<units::microwatt_t> {
  static constexpr auto name = const_name("wpimath.units.microwatts");
};

template <> struct unit_type_name<units::microwatts> {
  static constexpr auto name = const_name("wpimath.units.microwatts");
};

template <> struct unit_type_name<units::milliwatt_t> {
  static constexpr auto name = const_name("wpimath.units.milliwatts");
};

template <> struct unit_type_name<units::milliwatts> {
  static constexpr auto name = const_name("wpimath.units.milliwatts");
};

template <> struct unit_type_name<units::kilowatt_t> {
  static constexpr auto name = const_name("wpimath.units.kilowatts");
};

template <> struct unit_type_name<units::kilowatts> {
  static constexpr auto name = const_name("wpimath.units.kilowatts");
};

template <> struct unit_type_name<units::horsepower_t> {
  static constexpr auto name = const_name("wpimath.units.horsepower");
};

template <> struct unit_type_name<units::horsepower> {
  static constexpr auto name = const_name("wpimath.units.horsepower");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
