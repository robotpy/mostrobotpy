#pragma once

#include <units/charge.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::coulomb_t> {
  static constexpr auto name = const_name("wpimath.units.coulombs");
};

template <> struct unit_type_name<units::coulombs> {
  static constexpr auto name = const_name("wpimath.units.coulombs");
};

template <> struct unit_type_name<units::nanocoulomb_t> {
  static constexpr auto name = const_name("wpimath.units.nanocoulombs");
};

template <> struct unit_type_name<units::nanocoulombs> {
  static constexpr auto name = const_name("wpimath.units.nanocoulombs");
};

template <> struct unit_type_name<units::microcoulomb_t> {
  static constexpr auto name = const_name("wpimath.units.microcoulombs");
};

template <> struct unit_type_name<units::microcoulombs> {
  static constexpr auto name = const_name("wpimath.units.microcoulombs");
};

template <> struct unit_type_name<units::millicoulomb_t> {
  static constexpr auto name = const_name("wpimath.units.millicoulombs");
};

template <> struct unit_type_name<units::millicoulombs> {
  static constexpr auto name = const_name("wpimath.units.millicoulombs");
};

template <> struct unit_type_name<units::kilocoulomb_t> {
  static constexpr auto name = const_name("wpimath.units.kilocoulombs");
};

template <> struct unit_type_name<units::kilocoulombs> {
  static constexpr auto name = const_name("wpimath.units.kilocoulombs");
};

template <> struct unit_type_name<units::ampere_hour_t> {
  static constexpr auto name = const_name("wpimath.units.ampere_hours");
};

template <> struct unit_type_name<units::ampere_hours> {
  static constexpr auto name = const_name("wpimath.units.ampere_hours");
};

template <> struct unit_type_name<units::nanoampere_hour_t> {
  static constexpr auto name = const_name("wpimath.units.nanoampere_hours");
};

template <> struct unit_type_name<units::nanoampere_hours> {
  static constexpr auto name = const_name("wpimath.units.nanoampere_hours");
};

template <> struct unit_type_name<units::microampere_hour_t> {
  static constexpr auto name = const_name("wpimath.units.microampere_hours");
};

template <> struct unit_type_name<units::microampere_hours> {
  static constexpr auto name = const_name("wpimath.units.microampere_hours");
};

template <> struct unit_type_name<units::milliampere_hour_t> {
  static constexpr auto name = const_name("wpimath.units.milliampere_hours");
};

template <> struct unit_type_name<units::milliampere_hours> {
  static constexpr auto name = const_name("wpimath.units.milliampere_hours");
};

template <> struct unit_type_name<units::kiloampere_hour_t> {
  static constexpr auto name = const_name("wpimath.units.kiloampere_hours");
};

template <> struct unit_type_name<units::kiloampere_hours> {
  static constexpr auto name = const_name("wpimath.units.kiloampere_hours");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
