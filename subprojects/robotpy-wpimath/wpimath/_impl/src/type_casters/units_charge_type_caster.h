#pragma once

#include <units/charge.h>

namespace pybind11 {
namespace detail {
template <> struct handle_type_name<units::coulomb_t> {
  static constexpr auto name = _("coulombs");
};

template <> struct handle_type_name<units::coulombs> {
  static constexpr auto name = _("coulombs");
};

template <> struct handle_type_name<units::nanocoulomb_t> {
  static constexpr auto name = _("nanocoulombs");
};

template <> struct handle_type_name<units::nanocoulombs> {
  static constexpr auto name = _("nanocoulombs");
};

template <> struct handle_type_name<units::microcoulomb_t> {
  static constexpr auto name = _("microcoulombs");
};

template <> struct handle_type_name<units::microcoulombs> {
  static constexpr auto name = _("microcoulombs");
};

template <> struct handle_type_name<units::millicoulomb_t> {
  static constexpr auto name = _("millicoulombs");
};

template <> struct handle_type_name<units::millicoulombs> {
  static constexpr auto name = _("millicoulombs");
};

template <> struct handle_type_name<units::kilocoulomb_t> {
  static constexpr auto name = _("kilocoulombs");
};

template <> struct handle_type_name<units::kilocoulombs> {
  static constexpr auto name = _("kilocoulombs");
};

template <> struct handle_type_name<units::ampere_hour_t> {
  static constexpr auto name = _("ampere_hours");
};

template <> struct handle_type_name<units::ampere_hours> {
  static constexpr auto name = _("ampere_hours");
};

template <> struct handle_type_name<units::nanoampere_hour_t> {
  static constexpr auto name = _("nanoampere_hours");
};

template <> struct handle_type_name<units::nanoampere_hours> {
  static constexpr auto name = _("nanoampere_hours");
};

template <> struct handle_type_name<units::microampere_hour_t> {
  static constexpr auto name = _("microampere_hours");
};

template <> struct handle_type_name<units::microampere_hours> {
  static constexpr auto name = _("microampere_hours");
};

template <> struct handle_type_name<units::milliampere_hour_t> {
  static constexpr auto name = _("milliampere_hours");
};

template <> struct handle_type_name<units::milliampere_hours> {
  static constexpr auto name = _("milliampere_hours");
};

template <> struct handle_type_name<units::kiloampere_hour_t> {
  static constexpr auto name = _("kiloampere_hours");
};

template <> struct handle_type_name<units::kiloampere_hours> {
  static constexpr auto name = _("kiloampere_hours");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"
