#pragma once

#include <units/voltage.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::volt_t> {
  static constexpr auto name = const_name("wpimath.units.volts");
};

template <> struct unit_type_name<units::volts> {
  static constexpr auto name = const_name("wpimath.units.volts");
};

template <> struct unit_type_name<units::nanovolt_t> {
  static constexpr auto name = const_name("wpimath.units.nanovolts");
};

template <> struct unit_type_name<units::nanovolts> {
  static constexpr auto name = const_name("wpimath.units.nanovolts");
};

template <> struct unit_type_name<units::microvolt_t> {
  static constexpr auto name = const_name("wpimath.units.microvolts");
};

template <> struct unit_type_name<units::microvolts> {
  static constexpr auto name = const_name("wpimath.units.microvolts");
};

template <> struct unit_type_name<units::millivolt_t> {
  static constexpr auto name = const_name("wpimath.units.millivolts");
};

template <> struct unit_type_name<units::millivolts> {
  static constexpr auto name = const_name("wpimath.units.millivolts");
};

template <> struct unit_type_name<units::kilovolt_t> {
  static constexpr auto name = const_name("wpimath.units.kilovolts");
};

template <> struct unit_type_name<units::kilovolts> {
  static constexpr auto name = const_name("wpimath.units.kilovolts");
};

template <> struct unit_type_name<units::statvolt_t> {
  static constexpr auto name = const_name("wpimath.units.statvolts");
};

template <> struct unit_type_name<units::statvolts> {
  static constexpr auto name = const_name("wpimath.units.statvolts");
};

template <> struct unit_type_name<units::abvolt_t> {
  static constexpr auto name = const_name("wpimath.units.abvolts");
};

template <> struct unit_type_name<units::abvolts> {
  static constexpr auto name = const_name("wpimath.units.abvolts");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
