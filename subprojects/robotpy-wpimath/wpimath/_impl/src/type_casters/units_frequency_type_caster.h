#pragma once

#include <units/frequency.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::hertz_t> {
  static constexpr auto name = const_name("wpimath.units.hertz");
};

template <> struct unit_type_name<units::hertz> {
  static constexpr auto name = const_name("wpimath.units.hertz");
};

template <> struct unit_type_name<units::nanohertz_t> {
  static constexpr auto name = const_name("wpimath.units.nanohertz");
};

template <> struct unit_type_name<units::nanohertz> {
  static constexpr auto name = const_name("wpimath.units.nanohertz");
};

template <> struct unit_type_name<units::microhertz_t> {
  static constexpr auto name = const_name("wpimath.units.microhertz");
};

template <> struct unit_type_name<units::microhertz> {
  static constexpr auto name = const_name("wpimath.units.microhertz");
};

template <> struct unit_type_name<units::millihertz_t> {
  static constexpr auto name = const_name("wpimath.units.millihertz");
};

template <> struct unit_type_name<units::millihertz> {
  static constexpr auto name = const_name("wpimath.units.millihertz");
};

template <> struct unit_type_name<units::kilohertz_t> {
  static constexpr auto name = const_name("wpimath.units.kilohertz");
};

template <> struct unit_type_name<units::kilohertz> {
  static constexpr auto name = const_name("wpimath.units.kilohertz");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
