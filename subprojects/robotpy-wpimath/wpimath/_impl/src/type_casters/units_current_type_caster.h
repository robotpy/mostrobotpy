#pragma once

#include <units/current.h>

namespace pybind11 {
namespace detail {
template <> struct handle_type_name<units::ampere_t> {
  static constexpr auto name = _("amperes");
};

template <> struct handle_type_name<units::amperes> {
  static constexpr auto name = _("amperes");
};

template <> struct handle_type_name<units::nanoampere_t> {
  static constexpr auto name = _("nanoamperes");
};

template <> struct handle_type_name<units::nanoamperes> {
  static constexpr auto name = _("nanoamperes");
};

template <> struct handle_type_name<units::microampere_t> {
  static constexpr auto name = _("microamperes");
};

template <> struct handle_type_name<units::microamperes> {
  static constexpr auto name = _("microamperes");
};

template <> struct handle_type_name<units::milliampere_t> {
  static constexpr auto name = _("milliamperes");
};

template <> struct handle_type_name<units::milliamperes> {
  static constexpr auto name = _("milliamperes");
};

template <> struct handle_type_name<units::kiloampere_t> {
  static constexpr auto name = _("kiloamperes");
};

template <> struct handle_type_name<units::kiloamperes> {
  static constexpr auto name = _("kiloamperes");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"
