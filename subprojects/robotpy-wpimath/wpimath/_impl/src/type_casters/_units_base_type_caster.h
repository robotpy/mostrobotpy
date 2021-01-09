#pragma once

#include <pybind11/pybind11.h>

namespace pybind11 {
namespace detail {

template <class U, typename T, template <typename> class S>
struct type_caster<units::unit_t<U, T, S>> {
  using value_type = units::unit_t<U, T, S>;

  // TODO: there should be a way to include the type with this
  PYBIND11_TYPE_CASTER(value_type, handle_type_name<value_type>::name);

  bool load(handle src, bool convert) {
    if (!src)
      return false;
    if (!convert && !PyFloat_Check(src.ptr()))
      return false;
    value = value_type(PyFloat_AsDouble(src.ptr()));
    return true;
  }

  static handle cast(const value_type &src, return_value_policy /* policy */,
                     handle /* parent */) {
    return PyFloat_FromDouble(src.template to<double>());
  }
};

} // namespace detail
} // namespace pybind11