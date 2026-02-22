#pragma once

#include <units/current.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::ampere_t> {
  static constexpr auto name = const_name("wpimath.units.amperes");
};

template <> struct unit_type_name<units::amperes> {
  static constexpr auto name = const_name("wpimath.units.amperes");
};

template <> struct unit_type_name<units::nanoampere_t> {
  static constexpr auto name = const_name("wpimath.units.nanoamperes");
};

template <> struct unit_type_name<units::nanoamperes> {
  static constexpr auto name = const_name("wpimath.units.nanoamperes");
};

template <> struct unit_type_name<units::microampere_t> {
  static constexpr auto name = const_name("wpimath.units.microamperes");
};

template <> struct unit_type_name<units::microamperes> {
  static constexpr auto name = const_name("wpimath.units.microamperes");
};

template <> struct unit_type_name<units::milliampere_t> {
  static constexpr auto name = const_name("wpimath.units.milliamperes");
};

template <> struct unit_type_name<units::milliamperes> {
  static constexpr auto name = const_name("wpimath.units.milliamperes");
};

template <> struct unit_type_name<units::kiloampere_t> {
  static constexpr auto name = const_name("wpimath.units.kiloamperes");
};

template <> struct unit_type_name<units::kiloamperes> {
  static constexpr auto name = const_name("wpimath.units.kiloamperes");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
