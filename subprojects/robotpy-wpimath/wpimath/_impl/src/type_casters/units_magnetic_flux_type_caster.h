#pragma once

#include <units/magnetic_flux.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::weber_t> {
  static constexpr auto name = const_name("wpimath.units.webers");
};

template <> struct unit_type_name<units::webers> {
  static constexpr auto name = const_name("wpimath.units.webers");
};

template <> struct unit_type_name<units::nanoweber_t> {
  static constexpr auto name = const_name("wpimath.units.nanowebers");
};

template <> struct unit_type_name<units::nanowebers> {
  static constexpr auto name = const_name("wpimath.units.nanowebers");
};

template <> struct unit_type_name<units::microweber_t> {
  static constexpr auto name = const_name("wpimath.units.microwebers");
};

template <> struct unit_type_name<units::microwebers> {
  static constexpr auto name = const_name("wpimath.units.microwebers");
};

template <> struct unit_type_name<units::milliweber_t> {
  static constexpr auto name = const_name("wpimath.units.milliwebers");
};

template <> struct unit_type_name<units::milliwebers> {
  static constexpr auto name = const_name("wpimath.units.milliwebers");
};

template <> struct unit_type_name<units::kiloweber_t> {
  static constexpr auto name = const_name("wpimath.units.kilowebers");
};

template <> struct unit_type_name<units::kilowebers> {
  static constexpr auto name = const_name("wpimath.units.kilowebers");
};

template <> struct unit_type_name<units::maxwell_t> {
  static constexpr auto name = const_name("wpimath.units.maxwells");
};

template <> struct unit_type_name<units::maxwells> {
  static constexpr auto name = const_name("wpimath.units.maxwells");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
