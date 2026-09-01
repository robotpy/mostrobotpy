#pragma once

#include <pybind11/pybind11.h>

namespace wpi::tunables::python::annotations {

class TunableConfigObject : public pybind11::object {
 public:
  using pybind11::object::object;
};

class ComplexTunableObject : public pybind11::object {
 public:
  using pybind11::object::object;
};

}  // namespace wpi::tunables::python::annotations

namespace pybind11::detail {

template <>
struct handle_type_name<
    wpi::tunables::python::annotations::TunableConfigObject> {
  static constexpr auto name = const_name("TunableConfig");
};

template <>
struct handle_type_name<
    wpi::tunables::python::annotations::ComplexTunableObject> {
  static constexpr auto name = const_name("ComplexTunable");
};

}  // namespace pybind11::detail
