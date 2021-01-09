#pragma once

#include <units/force.h>

namespace pybind11 {
namespace detail {
template <> struct handle_type_name<units::newton_t> {
  static constexpr auto name = _("newtons");
};

template <> struct handle_type_name<units::newtons> {
  static constexpr auto name = _("newtons");
};

template <> struct handle_type_name<units::nanonewton_t> {
  static constexpr auto name = _("nanonewtons");
};

template <> struct handle_type_name<units::nanonewtons> {
  static constexpr auto name = _("nanonewtons");
};

template <> struct handle_type_name<units::micronewton_t> {
  static constexpr auto name = _("micronewtons");
};

template <> struct handle_type_name<units::micronewtons> {
  static constexpr auto name = _("micronewtons");
};

template <> struct handle_type_name<units::millinewton_t> {
  static constexpr auto name = _("millinewtons");
};

template <> struct handle_type_name<units::millinewtons> {
  static constexpr auto name = _("millinewtons");
};

template <> struct handle_type_name<units::kilonewton_t> {
  static constexpr auto name = _("kilonewtons");
};

template <> struct handle_type_name<units::kilonewtons> {
  static constexpr auto name = _("kilonewtons");
};

template <> struct handle_type_name<units::pound_t> {
  static constexpr auto name = _("pounds");
};

template <> struct handle_type_name<units::pounds> {
  static constexpr auto name = _("pounds");
};

template <> struct handle_type_name<units::dyne_t> {
  static constexpr auto name = _("dynes");
};

template <> struct handle_type_name<units::dynes> {
  static constexpr auto name = _("dynes");
};

template <> struct handle_type_name<units::kilopond_t> {
  static constexpr auto name = _("kiloponds");
};

template <> struct handle_type_name<units::kiloponds> {
  static constexpr auto name = _("kiloponds");
};

template <> struct handle_type_name<units::poundal_t> {
  static constexpr auto name = _("poundals");
};

template <> struct handle_type_name<units::poundals> {
  static constexpr auto name = _("poundals");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"
