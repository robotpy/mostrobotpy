#pragma once

#include <nanobind/nanobind.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

/*
  Units type caster assumptions

  When going from C++ to Python (eg, return values), the units that a user
  gets as a float are in whatever the unit was for C++.

    units::foot_t getFeet();    // converted to float, value is feet

  When going from Python to C++, the units a user uses are once again
  whatever the C++ function specifies:

    void setFeet(units::foot_t ft);   // must pass a float, it's in feet
    void setMeters(units::meter_t m); // must pass a float, it's in meters

  Unfortunately, with this type caster and robotpy-build there are mismatch
  issues with implicit conversions when default values are used that don't
  match the actual value:

    foo(units::second_t tm = 10_ms);    // if not careful, pybind11 will
                                        // store as 10 seconds
*/

template <typename T> struct unit_type_name {
  static constexpr auto name = const_name("float");
};

template <class U, typename T, template <typename> class S>
struct type_caster<units::unit_t<U, T, S>> {
  using value_type = units::unit_t<U, T, S>;

  NB_TYPE_CASTER(value_type, unit_type_name<value_type>::name);

  // Python -> C++
  bool from_python(handle src, uint8_t flags, cleanup_list *) noexcept {
    if (!src.is_valid()) {
      return false;
    }

    if (!(flags & (uint8_t)cast_flags::convert) && !PyFloat_Check(src.ptr())) {
      return false;
    }

    auto cvted = PyFloat_AsDouble(src.ptr());
    value = value_type(cvted);
    return !(cvted == -1 && PyErr_Occurred());
  }

  // C++ -> Python
  static handle from_cpp(const value_type &src, rv_policy,
                         cleanup_list *) noexcept {
    return PyFloat_FromDouble(src.template to<double>());
  }
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)
