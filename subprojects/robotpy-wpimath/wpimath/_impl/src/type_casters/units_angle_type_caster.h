#pragma once

#include <units/angle.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::radian_t> {
  static constexpr auto name = const_name("wpimath.units.radians");
};

template <> struct unit_type_name<units::radians> {
  static constexpr auto name = const_name("wpimath.units.radians");
};

template <> struct unit_type_name<units::nanoradian_t> {
  static constexpr auto name = const_name("wpimath.units.nanoradians");
};

template <> struct unit_type_name<units::nanoradians> {
  static constexpr auto name = const_name("wpimath.units.nanoradians");
};

template <> struct unit_type_name<units::microradian_t> {
  static constexpr auto name = const_name("wpimath.units.microradians");
};

template <> struct unit_type_name<units::microradians> {
  static constexpr auto name = const_name("wpimath.units.microradians");
};

template <> struct unit_type_name<units::milliradian_t> {
  static constexpr auto name = const_name("wpimath.units.milliradians");
};

template <> struct unit_type_name<units::milliradians> {
  static constexpr auto name = const_name("wpimath.units.milliradians");
};

template <> struct unit_type_name<units::kiloradian_t> {
  static constexpr auto name = const_name("wpimath.units.kiloradians");
};

template <> struct unit_type_name<units::kiloradians> {
  static constexpr auto name = const_name("wpimath.units.kiloradians");
};

template <> struct unit_type_name<units::degree_t> {
  static constexpr auto name = const_name("wpimath.units.degrees");
};

template <> struct unit_type_name<units::degrees> {
  static constexpr auto name = const_name("wpimath.units.degrees");
};

template <> struct unit_type_name<units::arcminute_t> {
  static constexpr auto name = const_name("wpimath.units.arcminutes");
};

template <> struct unit_type_name<units::arcminutes> {
  static constexpr auto name = const_name("wpimath.units.arcminutes");
};

template <> struct unit_type_name<units::arcsecond_t> {
  static constexpr auto name = const_name("wpimath.units.arcseconds");
};

template <> struct unit_type_name<units::arcseconds> {
  static constexpr auto name = const_name("wpimath.units.arcseconds");
};

template <> struct unit_type_name<units::milliarcsecond_t> {
  static constexpr auto name = const_name("wpimath.units.milliarcseconds");
};

template <> struct unit_type_name<units::milliarcseconds> {
  static constexpr auto name = const_name("wpimath.units.milliarcseconds");
};

template <> struct unit_type_name<units::turn_t> {
  static constexpr auto name = const_name("wpimath.units.turns");
};

template <> struct unit_type_name<units::turns> {
  static constexpr auto name = const_name("wpimath.units.turns");
};

template <> struct unit_type_name<units::gradian_t> {
  static constexpr auto name = const_name("wpimath.units.gradians");
};

template <> struct unit_type_name<units::gradians> {
  static constexpr auto name = const_name("wpimath.units.gradians");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
