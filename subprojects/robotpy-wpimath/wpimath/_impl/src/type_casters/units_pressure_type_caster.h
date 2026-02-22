#pragma once

#include <units/pressure.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::pascal_t> {
  static constexpr auto name = const_name("wpimath.units.pascals");
};

template <> struct unit_type_name<units::pascals> {
  static constexpr auto name = const_name("wpimath.units.pascals");
};

template <> struct unit_type_name<units::nanopascal_t> {
  static constexpr auto name = const_name("wpimath.units.nanopascals");
};

template <> struct unit_type_name<units::nanopascals> {
  static constexpr auto name = const_name("wpimath.units.nanopascals");
};

template <> struct unit_type_name<units::micropascal_t> {
  static constexpr auto name = const_name("wpimath.units.micropascals");
};

template <> struct unit_type_name<units::micropascals> {
  static constexpr auto name = const_name("wpimath.units.micropascals");
};

template <> struct unit_type_name<units::millipascal_t> {
  static constexpr auto name = const_name("wpimath.units.millipascals");
};

template <> struct unit_type_name<units::millipascals> {
  static constexpr auto name = const_name("wpimath.units.millipascals");
};

template <> struct unit_type_name<units::kilopascal_t> {
  static constexpr auto name = const_name("wpimath.units.kilopascals");
};

template <> struct unit_type_name<units::kilopascals> {
  static constexpr auto name = const_name("wpimath.units.kilopascals");
};

template <> struct unit_type_name<units::bar_t> {
  static constexpr auto name = const_name("wpimath.units.bars");
};

template <> struct unit_type_name<units::bars> {
  static constexpr auto name = const_name("wpimath.units.bars");
};

template <> struct unit_type_name<units::mbar_t> {
  static constexpr auto name = const_name("wpimath.units.mbars");
};

template <> struct unit_type_name<units::mbars> {
  static constexpr auto name = const_name("wpimath.units.mbars");
};

template <> struct unit_type_name<units::atmosphere_t> {
  static constexpr auto name = const_name("wpimath.units.atmospheres");
};

template <> struct unit_type_name<units::atmospheres> {
  static constexpr auto name = const_name("wpimath.units.atmospheres");
};

template <> struct unit_type_name<units::pounds_per_square_inch_t> {
  static constexpr auto name = const_name("wpimath.units.pounds_per_square_inch");
};

template <> struct unit_type_name<units::pounds_per_square_inch> {
  static constexpr auto name = const_name("wpimath.units.pounds_per_square_inch");
};

template <> struct unit_type_name<units::torr_t> {
  static constexpr auto name = const_name("wpimath.units.torrs");
};

template <> struct unit_type_name<units::torrs> {
  static constexpr auto name = const_name("wpimath.units.torrs");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
