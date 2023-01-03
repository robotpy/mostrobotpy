#pragma once

#include <robotpy_build.h>

// this assumes that the __hash__ of the python object isn't going to change
// once added to the map of the SelectCommand. This is... probably reasonable?
struct SelectCommandKey {

  SelectCommandKey() = default;
  ~SelectCommandKey() {
    py::gil_scoped_acquire gil;
    m_v.release().dec_ref();
  }

  SelectCommandKey(const SelectCommandKey& other) {
    py::gil_scoped_acquire gil;
    m_v = other.m_v;
    m_hash = py::hash(m_v);
  }

  SelectCommandKey &operator=(const SelectCommandKey& other) {
    py::gil_scoped_acquire gil;
    m_v = other.m_v;
    m_hash = py::hash(m_v);
    return *this;
  }

  SelectCommandKey &operator=(const py::handle src) {
    py::gil_scoped_acquire gil;
    m_v = py::reinterpret_borrow<py::object>(src);
    m_hash = py::hash(m_v);
    return *this;
  }

  operator py::object() const { return m_v; }

  py::object m_v;
  std::size_t m_hash;
};

inline bool operator==(const SelectCommandKey &lhs,
                       const SelectCommandKey &rhs) {
  py::gil_scoped_acquire gil;
  return lhs.m_v == rhs.m_v;
}

template <> struct std::hash<SelectCommandKey> {
  std::size_t operator()(const SelectCommandKey &s) const noexcept {
    return s.m_hash;
  }
};

namespace pybind11 {
namespace detail {
template <> struct type_caster<SelectCommandKey> {
  PYBIND11_TYPE_CASTER(SelectCommandKey, const_name("object"));
  bool load(handle src, bool) {
    value = src;
    return true;
  }

  static handle cast(const SelectCommandKey &src,
                     return_value_policy /* policy */, handle /* parent */) {
    return src.m_v;
  }
};
} // namespace detail
} // namespace pybind11
