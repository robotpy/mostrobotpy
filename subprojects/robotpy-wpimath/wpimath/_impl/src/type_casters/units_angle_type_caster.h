#pragma once

#include <units/angle.h>

namespace pybind11 {
namespace detail {
template <> struct handle_type_name<units::radian_t> {
  static constexpr auto name = _("radians");
};

template <> struct handle_type_name<units::radians> {
  static constexpr auto name = _("radians");
};

template <> struct handle_type_name<units::nanoradian_t> {
  static constexpr auto name = _("nanoradians");
};

template <> struct handle_type_name<units::nanoradians> {
  static constexpr auto name = _("nanoradians");
};

template <> struct handle_type_name<units::microradian_t> {
  static constexpr auto name = _("microradians");
};

template <> struct handle_type_name<units::microradians> {
  static constexpr auto name = _("microradians");
};

template <> struct handle_type_name<units::milliradian_t> {
  static constexpr auto name = _("milliradians");
};

template <> struct handle_type_name<units::milliradians> {
  static constexpr auto name = _("milliradians");
};

template <> struct handle_type_name<units::kiloradian_t> {
  static constexpr auto name = _("kiloradians");
};

template <> struct handle_type_name<units::kiloradians> {
  static constexpr auto name = _("kiloradians");
};

template <> struct handle_type_name<units::degree_t> {
  static constexpr auto name = _("degrees");
};

template <> struct handle_type_name<units::degrees> {
  static constexpr auto name = _("degrees");
};

template <> struct handle_type_name<units::arcminute_t> {
  static constexpr auto name = _("arcminutes");
};

template <> struct handle_type_name<units::arcminutes> {
  static constexpr auto name = _("arcminutes");
};

template <> struct handle_type_name<units::arcsecond_t> {
  static constexpr auto name = _("arcseconds");
};

template <> struct handle_type_name<units::arcseconds> {
  static constexpr auto name = _("arcseconds");
};

template <> struct handle_type_name<units::milliarcsecond_t> {
  static constexpr auto name = _("milliarcseconds");
};

template <> struct handle_type_name<units::milliarcseconds> {
  static constexpr auto name = _("milliarcseconds");
};

template <> struct handle_type_name<units::turn_t> {
  static constexpr auto name = _("turns");
};

template <> struct handle_type_name<units::turns> {
  static constexpr auto name = _("turns");
};

template <> struct handle_type_name<units::gradian_t> {
  static constexpr auto name = _("gradians");
};

template <> struct handle_type_name<units::gradians> {
  static constexpr auto name = _("gradians");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"
