#pragma once

#include <units/torque.h>

namespace pybind11 {
namespace detail {
template <> struct handle_type_name<units::newton_meter_t> {
  static constexpr auto name = _("newton_meters");
};

template <> struct handle_type_name<units::newton_meters> {
  static constexpr auto name = _("newton_meters");
};

// template <> struct handle_type_name<units::foot_pound_t> {
//   static constexpr auto name = _("foot_pounds");
// };

// template <> struct handle_type_name<units::foot_pounds> {
//   static constexpr auto name = _("foot_pounds");
// };

template <> struct handle_type_name<units::foot_poundal_t> {
  static constexpr auto name = _("foot_poundals");
};

template <> struct handle_type_name<units::foot_poundals> {
  static constexpr auto name = _("foot_poundals");
};

template <> struct handle_type_name<units::inch_pound_t> {
  static constexpr auto name = _("inch_pounds");
};

template <> struct handle_type_name<units::inch_pounds> {
  static constexpr auto name = _("inch_pounds");
};

template <> struct handle_type_name<units::meter_kilogram_t> {
  static constexpr auto name = _("meter_kilograms");
};

template <> struct handle_type_name<units::meter_kilograms> {
  static constexpr auto name = _("meter_kilograms");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"
