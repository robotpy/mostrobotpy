#pragma once

#include <units/luminous_flux.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::lumen_t> {
  static constexpr auto name = const_name("wpimath.units.lumens");
};

template <> struct unit_type_name<units::lumens> {
  static constexpr auto name = const_name("wpimath.units.lumens");
};

template <> struct unit_type_name<units::nanolumen_t> {
  static constexpr auto name = const_name("wpimath.units.nanolumens");
};

template <> struct unit_type_name<units::nanolumens> {
  static constexpr auto name = const_name("wpimath.units.nanolumens");
};

template <> struct unit_type_name<units::microlumen_t> {
  static constexpr auto name = const_name("wpimath.units.microlumens");
};

template <> struct unit_type_name<units::microlumens> {
  static constexpr auto name = const_name("wpimath.units.microlumens");
};

template <> struct unit_type_name<units::millilumen_t> {
  static constexpr auto name = const_name("wpimath.units.millilumens");
};

template <> struct unit_type_name<units::millilumens> {
  static constexpr auto name = const_name("wpimath.units.millilumens");
};

template <> struct unit_type_name<units::kilolumen_t> {
  static constexpr auto name = const_name("wpimath.units.kilolumens");
};

template <> struct unit_type_name<units::kilolumens> {
  static constexpr auto name = const_name("wpimath.units.kilolumens");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
