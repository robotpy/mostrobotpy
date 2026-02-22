#pragma once

#include <units/torque.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::newton_meter_t> {
  static constexpr auto name = const_name("wpimath.units.newton_meters");
};

template <> struct unit_type_name<units::newton_meters> {
  static constexpr auto name = const_name("wpimath.units.newton_meters");
};

// template <> struct unit_type_name<units::foot_pound_t> {
//   static constexpr auto name = const_name("wpimath.units.foot_pounds");
// };

// template <> struct unit_type_name<units::foot_pounds> {
//   static constexpr auto name = const_name("wpimath.units.foot_pounds");
// };

template <> struct unit_type_name<units::foot_poundal_t> {
  static constexpr auto name = const_name("wpimath.units.foot_poundals");
};

template <> struct unit_type_name<units::foot_poundals> {
  static constexpr auto name = const_name("wpimath.units.foot_poundals");
};

template <> struct unit_type_name<units::inch_pound_t> {
  static constexpr auto name = const_name("wpimath.units.inch_pounds");
};

template <> struct unit_type_name<units::inch_pounds> {
  static constexpr auto name = const_name("wpimath.units.inch_pounds");
};

template <> struct unit_type_name<units::meter_kilogram_t> {
  static constexpr auto name = const_name("wpimath.units.meter_kilograms");
};

template <> struct unit_type_name<units::meter_kilograms> {
  static constexpr auto name = const_name("wpimath.units.meter_kilograms");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
