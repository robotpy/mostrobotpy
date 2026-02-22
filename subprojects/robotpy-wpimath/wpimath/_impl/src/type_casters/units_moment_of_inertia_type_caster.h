#pragma once

#include <units/moment_of_inertia.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::kilogram_square_meter_t> {
  static constexpr auto name = const_name("wpimath.units.kilogram_square_meters");
};

template <> struct unit_type_name<units::kilogram_square_meters> {
  static constexpr auto name = const_name("wpimath.units.kilogram_square_meters");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
