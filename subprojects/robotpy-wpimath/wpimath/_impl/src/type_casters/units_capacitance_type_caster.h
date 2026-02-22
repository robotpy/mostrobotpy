#pragma once

#include <units/capacitance.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::farad_t> {
  static constexpr auto name = const_name("wpimath.units.farads");
};

template <> struct unit_type_name<units::farads> {
  static constexpr auto name = const_name("wpimath.units.farads");
};

template <> struct unit_type_name<units::nanofarad_t> {
  static constexpr auto name = const_name("wpimath.units.nanofarads");
};

template <> struct unit_type_name<units::nanofarads> {
  static constexpr auto name = const_name("wpimath.units.nanofarads");
};

template <> struct unit_type_name<units::microfarad_t> {
  static constexpr auto name = const_name("wpimath.units.microfarads");
};

template <> struct unit_type_name<units::microfarads> {
  static constexpr auto name = const_name("wpimath.units.microfarads");
};

template <> struct unit_type_name<units::millifarad_t> {
  static constexpr auto name = const_name("wpimath.units.millifarads");
};

template <> struct unit_type_name<units::millifarads> {
  static constexpr auto name = const_name("wpimath.units.millifarads");
};

template <> struct unit_type_name<units::kilofarad_t> {
  static constexpr auto name = const_name("wpimath.units.kilofarads");
};

template <> struct unit_type_name<units::kilofarads> {
  static constexpr auto name = const_name("wpimath.units.kilofarads");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
