#pragma once

#include <units/pressure.h>

namespace pybind11 {
namespace detail {
template <> struct handle_type_name<units::pascal_t> {
  static constexpr auto name = _("pascals");
};

template <> struct handle_type_name<units::pascals> {
  static constexpr auto name = _("pascals");
};

template <> struct handle_type_name<units::nanopascal_t> {
  static constexpr auto name = _("nanopascals");
};

template <> struct handle_type_name<units::nanopascals> {
  static constexpr auto name = _("nanopascals");
};

template <> struct handle_type_name<units::micropascal_t> {
  static constexpr auto name = _("micropascals");
};

template <> struct handle_type_name<units::micropascals> {
  static constexpr auto name = _("micropascals");
};

template <> struct handle_type_name<units::millipascal_t> {
  static constexpr auto name = _("millipascals");
};

template <> struct handle_type_name<units::millipascals> {
  static constexpr auto name = _("millipascals");
};

template <> struct handle_type_name<units::kilopascal_t> {
  static constexpr auto name = _("kilopascals");
};

template <> struct handle_type_name<units::kilopascals> {
  static constexpr auto name = _("kilopascals");
};

template <> struct handle_type_name<units::bar_t> {
  static constexpr auto name = _("bars");
};

template <> struct handle_type_name<units::bars> {
  static constexpr auto name = _("bars");
};

template <> struct handle_type_name<units::mbar_t> {
  static constexpr auto name = _("mbars");
};

template <> struct handle_type_name<units::mbars> {
  static constexpr auto name = _("mbars");
};

template <> struct handle_type_name<units::atmosphere_t> {
  static constexpr auto name = _("atmospheres");
};

template <> struct handle_type_name<units::atmospheres> {
  static constexpr auto name = _("atmospheres");
};

template <> struct handle_type_name<units::pounds_per_square_inch_t> {
  static constexpr auto name = _("pounds_per_square_inch");
};

template <> struct handle_type_name<units::pounds_per_square_inch> {
  static constexpr auto name = _("pounds_per_square_inch");
};

template <> struct handle_type_name<units::torr_t> {
  static constexpr auto name = _("torrs");
};

template <> struct handle_type_name<units::torrs> {
  static constexpr auto name = _("torrs");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"
