#pragma once

#include <units/data_transfer_rate.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::exabytes_per_second_t> {
  static constexpr auto name = const_name("wpimath.units.exabytes_per_second");
};

template <> struct unit_type_name<units::exabytes_per_second> {
  static constexpr auto name = const_name("wpimath.units.exabytes_per_second");
};

template <> struct unit_type_name<units::exabits_per_second_t> {
  static constexpr auto name = const_name("wpimath.units.exabits_per_second");
};

template <> struct unit_type_name<units::exabits_per_second> {
  static constexpr auto name = const_name("wpimath.units.exabits_per_second");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
