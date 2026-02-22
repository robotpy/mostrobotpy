#pragma once

#include <units/illuminance.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::lux_t> {
  static constexpr auto name = const_name("wpimath.units.luxes");
};

template <> struct unit_type_name<units::luxes> {
  static constexpr auto name = const_name("wpimath.units.luxes");
};

template <> struct unit_type_name<units::nanolux_t> {
  static constexpr auto name = const_name("wpimath.units.nanoluxes");
};

template <> struct unit_type_name<units::nanoluxes> {
  static constexpr auto name = const_name("wpimath.units.nanoluxes");
};

template <> struct unit_type_name<units::microlux_t> {
  static constexpr auto name = const_name("wpimath.units.microluxes");
};

template <> struct unit_type_name<units::microluxes> {
  static constexpr auto name = const_name("wpimath.units.microluxes");
};

template <> struct unit_type_name<units::millilux_t> {
  static constexpr auto name = const_name("wpimath.units.milliluxes");
};

template <> struct unit_type_name<units::milliluxes> {
  static constexpr auto name = const_name("wpimath.units.milliluxes");
};

template <> struct unit_type_name<units::kilolux_t> {
  static constexpr auto name = const_name("wpimath.units.kiloluxes");
};

template <> struct unit_type_name<units::kiloluxes> {
  static constexpr auto name = const_name("wpimath.units.kiloluxes");
};

template <> struct unit_type_name<units::footcandle_t> {
  static constexpr auto name = const_name("wpimath.units.footcandles");
};

template <> struct unit_type_name<units::footcandles> {
  static constexpr auto name = const_name("wpimath.units.footcandles");
};

template <> struct unit_type_name<units::lumens_per_square_inch_t> {
  static constexpr auto name = const_name("wpimath.units.lumens_per_square_inch");
};

template <> struct unit_type_name<units::lumens_per_square_inch> {
  static constexpr auto name = const_name("wpimath.units.lumens_per_square_inch");
};

template <> struct unit_type_name<units::phot_t> {
  static constexpr auto name = const_name("wpimath.units.phots");
};

template <> struct unit_type_name<units::phots> {
  static constexpr auto name = const_name("wpimath.units.phots");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
