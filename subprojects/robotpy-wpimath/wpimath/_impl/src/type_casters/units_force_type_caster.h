#pragma once

#include <units/force.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;

template <> struct unit_type_name<units::newton_t> {
  static constexpr auto name = const_name("wpimath.units.newtons");
};

template <> struct unit_type_name<units::newtons> {
  static constexpr auto name = const_name("wpimath.units.newtons");
};

template <> struct unit_type_name<units::nanonewton_t> {
  static constexpr auto name = const_name("wpimath.units.nanonewtons");
};

template <> struct unit_type_name<units::nanonewtons> {
  static constexpr auto name = const_name("wpimath.units.nanonewtons");
};

template <> struct unit_type_name<units::micronewton_t> {
  static constexpr auto name = const_name("wpimath.units.micronewtons");
};

template <> struct unit_type_name<units::micronewtons> {
  static constexpr auto name = const_name("wpimath.units.micronewtons");
};

template <> struct unit_type_name<units::millinewton_t> {
  static constexpr auto name = const_name("wpimath.units.millinewtons");
};

template <> struct unit_type_name<units::millinewtons> {
  static constexpr auto name = const_name("wpimath.units.millinewtons");
};

template <> struct unit_type_name<units::kilonewton_t> {
  static constexpr auto name = const_name("wpimath.units.kilonewtons");
};

template <> struct unit_type_name<units::kilonewtons> {
  static constexpr auto name = const_name("wpimath.units.kilonewtons");
};

template <> struct unit_type_name<units::pound_t> {
  static constexpr auto name = const_name("wpimath.units.pounds");
};

template <> struct unit_type_name<units::pounds> {
  static constexpr auto name = const_name("wpimath.units.pounds");
};

template <> struct unit_type_name<units::dyne_t> {
  static constexpr auto name = const_name("wpimath.units.dynes");
};

template <> struct unit_type_name<units::dynes> {
  static constexpr auto name = const_name("wpimath.units.dynes");
};

template <> struct unit_type_name<units::kilopond_t> {
  static constexpr auto name = const_name("wpimath.units.kiloponds");
};

template <> struct unit_type_name<units::kiloponds> {
  static constexpr auto name = const_name("wpimath.units.kiloponds");
};

template <> struct unit_type_name<units::poundal_t> {
  static constexpr auto name = const_name("wpimath.units.poundals");
};

template <> struct unit_type_name<units::poundals> {
  static constexpr auto name = const_name("wpimath.units.poundals");
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"
