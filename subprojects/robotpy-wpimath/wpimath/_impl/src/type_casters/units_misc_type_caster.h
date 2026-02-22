#pragma once

#include <units/mass.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename T> struct unit_type_name;


template <> struct unit_type_name<units::dimensionless::scalar_t> {
  static constexpr auto name = const_name("float");
};

template <> struct unit_type_name<units::dimensionless::scalar> {
  static constexpr auto name = const_name("float");
};

// template <> struct unit_type_name<units::dimensionless::dimensionless_t> {
//   static constexpr auto name = const_name("float");
// };

// template <> struct unit_type_name<units::dimensionless::dimensionless> {
//   static constexpr auto name = const_name("float");
// };

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

#include "_units_base_type_caster.h"