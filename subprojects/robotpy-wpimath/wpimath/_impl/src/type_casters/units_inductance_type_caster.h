#pragma once

#include <units/inductance.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::henry_t> {
  static constexpr auto name = const_name("wpimath.units.henries");
};

template <> struct unit_type_name<units::henries> {
  static constexpr auto name = const_name("wpimath.units.henries");
};

template <> struct unit_type_name<units::nanohenry_t> {
  static constexpr auto name = const_name("wpimath.units.nanohenries");
};

template <> struct unit_type_name<units::nanohenries> {
  static constexpr auto name = const_name("wpimath.units.nanohenries");
};

template <> struct unit_type_name<units::microhenry_t> {
  static constexpr auto name = const_name("wpimath.units.microhenries");
};

template <> struct unit_type_name<units::microhenries> {
  static constexpr auto name = const_name("wpimath.units.microhenries");
};

template <> struct unit_type_name<units::millihenry_t> {
  static constexpr auto name = const_name("wpimath.units.millihenries");
};

template <> struct unit_type_name<units::millihenries> {
  static constexpr auto name = const_name("wpimath.units.millihenries");
};

template <> struct unit_type_name<units::kilohenry_t> {
  static constexpr auto name = const_name("wpimath.units.kilohenries");
};

template <> struct unit_type_name<units::kilohenries> {
  static constexpr auto name = const_name("wpimath.units.kilohenries");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
