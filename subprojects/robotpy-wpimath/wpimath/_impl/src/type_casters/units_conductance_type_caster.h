#pragma once

#include <units/conductance.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::siemens_t> {
  static constexpr auto name = const_name("wpimath.units.siemens");
};

template <> struct unit_type_name<units::siemens> {
  static constexpr auto name = const_name("wpimath.units.siemens");
};

template <> struct unit_type_name<units::nanosiemens_t> {
  static constexpr auto name = const_name("wpimath.units.nanosiemens");
};

template <> struct unit_type_name<units::nanosiemens> {
  static constexpr auto name = const_name("wpimath.units.nanosiemens");
};

template <> struct unit_type_name<units::microsiemens_t> {
  static constexpr auto name = const_name("wpimath.units.microsiemens");
};

template <> struct unit_type_name<units::microsiemens> {
  static constexpr auto name = const_name("wpimath.units.microsiemens");
};

template <> struct unit_type_name<units::millisiemens_t> {
  static constexpr auto name = const_name("wpimath.units.millisiemens");
};

template <> struct unit_type_name<units::millisiemens> {
  static constexpr auto name = const_name("wpimath.units.millisiemens");
};

template <> struct unit_type_name<units::kilosiemens_t> {
  static constexpr auto name = const_name("wpimath.units.kilosiemens");
};

template <> struct unit_type_name<units::kilosiemens> {
  static constexpr auto name = const_name("wpimath.units.kilosiemens");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
