#pragma once

#include <units/area.h>

namespace pybind11 {
namespace detail {
template <> struct handle_type_name<units::square_meter_t> {
  static constexpr auto name = _("square_meters");
};

template <> struct handle_type_name<units::square_meters> {
  static constexpr auto name = _("square_meters");
};

template <> struct handle_type_name<units::square_foot_t> {
  static constexpr auto name = _("square_feet");
};

template <> struct handle_type_name<units::square_feet> {
  static constexpr auto name = _("square_feet");
};

template <> struct handle_type_name<units::square_inch_t> {
  static constexpr auto name = _("square_inches");
};

template <> struct handle_type_name<units::square_inches> {
  static constexpr auto name = _("square_inches");
};

template <> struct handle_type_name<units::square_mile_t> {
  static constexpr auto name = _("square_miles");
};

template <> struct handle_type_name<units::square_miles> {
  static constexpr auto name = _("square_miles");
};

template <> struct handle_type_name<units::square_kilometer_t> {
  static constexpr auto name = _("square_kilometers");
};

template <> struct handle_type_name<units::square_kilometers> {
  static constexpr auto name = _("square_kilometers");
};

template <> struct handle_type_name<units::hectare_t> {
  static constexpr auto name = _("hectares");
};

template <> struct handle_type_name<units::hectares> {
  static constexpr auto name = _("hectares");
};

template <> struct handle_type_name<units::acre_t> {
  static constexpr auto name = _("acres");
};

template <> struct handle_type_name<units::acres> {
  static constexpr auto name = _("acres");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"
