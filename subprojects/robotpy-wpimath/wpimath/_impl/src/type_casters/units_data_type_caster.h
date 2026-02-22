#pragma once

#include <units/data.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::exabyte_t> {
  static constexpr auto name = const_name("wpimath.units.exabytes");
};

template <> struct unit_type_name<units::exabytes> {
  static constexpr auto name = const_name("wpimath.units.exabytes");
};

template <> struct unit_type_name<units::exabit_t> {
  static constexpr auto name = const_name("wpimath.units.exabits");
};

template <> struct unit_type_name<units::exabits> {
  static constexpr auto name = const_name("wpimath.units.exabits");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
