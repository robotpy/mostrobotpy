#pragma once

#include <units/substance.h>

namespace pybind11 {
namespace detail {
template <> struct handle_type_name<units::mole_t> {
  static constexpr auto name = _("moles");
};

template <> struct handle_type_name<units::moles> {
  static constexpr auto name = _("moles");
};

} // namespace detail
} // namespace pybind11

#include "_units_base_type_caster.h"
