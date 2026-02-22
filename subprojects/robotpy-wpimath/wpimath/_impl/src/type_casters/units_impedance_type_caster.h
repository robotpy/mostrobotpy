#pragma once

#include <units/impedance.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::ohm_t> {
  static constexpr auto name = const_name("wpimath.units.ohms");
};

template <> struct unit_type_name<units::ohms> {
  static constexpr auto name = const_name("wpimath.units.ohms");
};

template <> struct unit_type_name<units::nanoohm_t> {
  static constexpr auto name = const_name("wpimath.units.nanoohms");
};

template <> struct unit_type_name<units::nanoohms> {
  static constexpr auto name = const_name("wpimath.units.nanoohms");
};

template <> struct unit_type_name<units::microohm_t> {
  static constexpr auto name = const_name("wpimath.units.microohms");
};

template <> struct unit_type_name<units::microohms> {
  static constexpr auto name = const_name("wpimath.units.microohms");
};

template <> struct unit_type_name<units::milliohm_t> {
  static constexpr auto name = const_name("wpimath.units.milliohms");
};

template <> struct unit_type_name<units::milliohms> {
  static constexpr auto name = const_name("wpimath.units.milliohms");
};

template <> struct unit_type_name<units::kiloohm_t> {
  static constexpr auto name = const_name("wpimath.units.kiloohms");
};

template <> struct unit_type_name<units::kiloohms> {
  static constexpr auto name = const_name("wpimath.units.kiloohms");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
