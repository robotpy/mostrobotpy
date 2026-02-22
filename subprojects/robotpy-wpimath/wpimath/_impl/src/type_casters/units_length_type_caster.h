#pragma once

#include <units/length.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::meter_t> {
  static constexpr auto name = const_name("wpimath.units.meters");
};

template <> struct unit_type_name<units::meters> {
  static constexpr auto name = const_name("wpimath.units.meters");
};

template <> struct unit_type_name<units::nanometer_t> {
  static constexpr auto name = const_name("wpimath.units.nanometers");
};

template <> struct unit_type_name<units::nanometers> {
  static constexpr auto name = const_name("wpimath.units.nanometers");
};

template <> struct unit_type_name<units::micrometer_t> {
  static constexpr auto name = const_name("wpimath.units.micrometers");
};

template <> struct unit_type_name<units::micrometers> {
  static constexpr auto name = const_name("wpimath.units.micrometers");
};

template <> struct unit_type_name<units::millimeter_t> {
  static constexpr auto name = const_name("wpimath.units.millimeters");
};

template <> struct unit_type_name<units::millimeters> {
  static constexpr auto name = const_name("wpimath.units.millimeters");
};

template <> struct unit_type_name<units::centimeter_t> {
  static constexpr auto name = const_name("wpimath.units.centimeters");
};

template <> struct unit_type_name<units::centimeters> {
  static constexpr auto name = const_name("wpimath.units.centimeters");
};

template <> struct unit_type_name<units::kilometer_t> {
  static constexpr auto name = const_name("wpimath.units.kilometers");
};

template <> struct unit_type_name<units::kilometers> {
  static constexpr auto name = const_name("wpimath.units.kilometers");
};

template <> struct unit_type_name<units::foot_t> {
  static constexpr auto name = const_name("wpimath.units.feet");
};

template <> struct unit_type_name<units::feet> {
  static constexpr auto name = const_name("wpimath.units.feet");
};

template <> struct unit_type_name<units::mil_t> {
  static constexpr auto name = const_name("wpimath.units.mils");
};

template <> struct unit_type_name<units::mils> {
  static constexpr auto name = const_name("wpimath.units.mils");
};

template <> struct unit_type_name<units::inch_t> {
  static constexpr auto name = const_name("wpimath.units.inches");
};

template <> struct unit_type_name<units::inches> {
  static constexpr auto name = const_name("wpimath.units.inches");
};

template <> struct unit_type_name<units::mile_t> {
  static constexpr auto name = const_name("wpimath.units.miles");
};

template <> struct unit_type_name<units::miles> {
  static constexpr auto name = const_name("wpimath.units.miles");
};

template <> struct unit_type_name<units::nauticalMile_t> {
  static constexpr auto name = const_name("wpimath.units.nauticalMiles");
};

template <> struct unit_type_name<units::nauticalMiles> {
  static constexpr auto name = const_name("wpimath.units.nauticalMiles");
};

template <> struct unit_type_name<units::astronicalUnit_t> {
  static constexpr auto name = const_name("wpimath.units.astronicalUnits");
};

template <> struct unit_type_name<units::astronicalUnits> {
  static constexpr auto name = const_name("wpimath.units.astronicalUnits");
};

template <> struct unit_type_name<units::lightyear_t> {
  static constexpr auto name = const_name("wpimath.units.lightyears");
};

template <> struct unit_type_name<units::lightyears> {
  static constexpr auto name = const_name("wpimath.units.lightyears");
};

template <> struct unit_type_name<units::parsec_t> {
  static constexpr auto name = const_name("wpimath.units.parsecs");
};

template <> struct unit_type_name<units::parsecs> {
  static constexpr auto name = const_name("wpimath.units.parsecs");
};

template <> struct unit_type_name<units::angstrom_t> {
  static constexpr auto name = const_name("wpimath.units.angstroms");
};

template <> struct unit_type_name<units::angstroms> {
  static constexpr auto name = const_name("wpimath.units.angstroms");
};

template <> struct unit_type_name<units::cubit_t> {
  static constexpr auto name = const_name("wpimath.units.cubits");
};

template <> struct unit_type_name<units::cubits> {
  static constexpr auto name = const_name("wpimath.units.cubits");
};

template <> struct unit_type_name<units::fathom_t> {
  static constexpr auto name = const_name("wpimath.units.fathoms");
};

template <> struct unit_type_name<units::fathoms> {
  static constexpr auto name = const_name("wpimath.units.fathoms");
};

template <> struct unit_type_name<units::chain_t> {
  static constexpr auto name = const_name("wpimath.units.chains");
};

template <> struct unit_type_name<units::chains> {
  static constexpr auto name = const_name("wpimath.units.chains");
};

template <> struct unit_type_name<units::furlong_t> {
  static constexpr auto name = const_name("wpimath.units.furlongs");
};

template <> struct unit_type_name<units::furlongs> {
  static constexpr auto name = const_name("wpimath.units.furlongs");
};

template <> struct unit_type_name<units::hand_t> {
  static constexpr auto name = const_name("wpimath.units.hands");
};

template <> struct unit_type_name<units::hands> {
  static constexpr auto name = const_name("wpimath.units.hands");
};

template <> struct unit_type_name<units::league_t> {
  static constexpr auto name = const_name("wpimath.units.leagues");
};

template <> struct unit_type_name<units::leagues> {
  static constexpr auto name = const_name("wpimath.units.leagues");
};

template <> struct unit_type_name<units::nauticalLeague_t> {
  static constexpr auto name = const_name("wpimath.units.nauticalLeagues");
};

template <> struct unit_type_name<units::nauticalLeagues> {
  static constexpr auto name = const_name("wpimath.units.nauticalLeagues");
};

template <> struct unit_type_name<units::yard_t> {
  static constexpr auto name = const_name("wpimath.units.yards");
};

template <> struct unit_type_name<units::yards> {
  static constexpr auto name = const_name("wpimath.units.yards");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
