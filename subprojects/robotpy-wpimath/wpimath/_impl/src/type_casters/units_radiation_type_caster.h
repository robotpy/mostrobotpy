#pragma once

#include <units/radiation.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::becquerel_t> {
  static constexpr auto name = const_name("wpimath.units.becquerels");
};

template <> struct unit_type_name<units::becquerels> {
  static constexpr auto name = const_name("wpimath.units.becquerels");
};

template <> struct unit_type_name<units::nanobecquerel_t> {
  static constexpr auto name = const_name("wpimath.units.nanobecquerels");
};

template <> struct unit_type_name<units::nanobecquerels> {
  static constexpr auto name = const_name("wpimath.units.nanobecquerels");
};

template <> struct unit_type_name<units::microbecquerel_t> {
  static constexpr auto name = const_name("wpimath.units.microbecquerels");
};

template <> struct unit_type_name<units::microbecquerels> {
  static constexpr auto name = const_name("wpimath.units.microbecquerels");
};

template <> struct unit_type_name<units::millibecquerel_t> {
  static constexpr auto name = const_name("wpimath.units.millibecquerels");
};

template <> struct unit_type_name<units::millibecquerels> {
  static constexpr auto name = const_name("wpimath.units.millibecquerels");
};

template <> struct unit_type_name<units::kilobecquerel_t> {
  static constexpr auto name = const_name("wpimath.units.kilobecquerels");
};

template <> struct unit_type_name<units::kilobecquerels> {
  static constexpr auto name = const_name("wpimath.units.kilobecquerels");
};

template <> struct unit_type_name<units::gray_t> {
  static constexpr auto name = const_name("wpimath.units.grays");
};

template <> struct unit_type_name<units::grays> {
  static constexpr auto name = const_name("wpimath.units.grays");
};

template <> struct unit_type_name<units::nanogray_t> {
  static constexpr auto name = const_name("wpimath.units.nanograys");
};

template <> struct unit_type_name<units::nanograys> {
  static constexpr auto name = const_name("wpimath.units.nanograys");
};

template <> struct unit_type_name<units::microgray_t> {
  static constexpr auto name = const_name("wpimath.units.micrograys");
};

template <> struct unit_type_name<units::micrograys> {
  static constexpr auto name = const_name("wpimath.units.micrograys");
};

template <> struct unit_type_name<units::milligray_t> {
  static constexpr auto name = const_name("wpimath.units.milligrays");
};

template <> struct unit_type_name<units::milligrays> {
  static constexpr auto name = const_name("wpimath.units.milligrays");
};

template <> struct unit_type_name<units::kilogray_t> {
  static constexpr auto name = const_name("wpimath.units.kilograys");
};

template <> struct unit_type_name<units::kilograys> {
  static constexpr auto name = const_name("wpimath.units.kilograys");
};

template <> struct unit_type_name<units::sievert_t> {
  static constexpr auto name = const_name("wpimath.units.sieverts");
};

template <> struct unit_type_name<units::sieverts> {
  static constexpr auto name = const_name("wpimath.units.sieverts");
};

template <> struct unit_type_name<units::nanosievert_t> {
  static constexpr auto name = const_name("wpimath.units.nanosieverts");
};

template <> struct unit_type_name<units::nanosieverts> {
  static constexpr auto name = const_name("wpimath.units.nanosieverts");
};

template <> struct unit_type_name<units::microsievert_t> {
  static constexpr auto name = const_name("wpimath.units.microsieverts");
};

template <> struct unit_type_name<units::microsieverts> {
  static constexpr auto name = const_name("wpimath.units.microsieverts");
};

template <> struct unit_type_name<units::millisievert_t> {
  static constexpr auto name = const_name("wpimath.units.millisieverts");
};

template <> struct unit_type_name<units::millisieverts> {
  static constexpr auto name = const_name("wpimath.units.millisieverts");
};

template <> struct unit_type_name<units::kilosievert_t> {
  static constexpr auto name = const_name("wpimath.units.kilosieverts");
};

template <> struct unit_type_name<units::kilosieverts> {
  static constexpr auto name = const_name("wpimath.units.kilosieverts");
};

template <> struct unit_type_name<units::curie_t> {
  static constexpr auto name = const_name("wpimath.units.curies");
};

template <> struct unit_type_name<units::curies> {
  static constexpr auto name = const_name("wpimath.units.curies");
};

template <> struct unit_type_name<units::rutherford_t> {
  static constexpr auto name = const_name("wpimath.units.rutherfords");
};

template <> struct unit_type_name<units::rutherfords> {
  static constexpr auto name = const_name("wpimath.units.rutherfords");
};

template <> struct unit_type_name<units::rad_t> {
  static constexpr auto name = const_name("wpimath.units.rads");
};

template <> struct unit_type_name<units::rads> {
  static constexpr auto name = const_name("wpimath.units.rads");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
