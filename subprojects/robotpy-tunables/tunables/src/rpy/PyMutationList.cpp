#include "PyMutationList.h"

#include <string>
#include <utility>

namespace py = pybind11;

namespace wpi::tunables::python {

PyMutationList::PyMutationList(std::shared_ptr<PyTunable> owner, py::list data)
    : m_owner{std::move(owner)}, m_data{std::move(data)} {}

size_t PyMutationList::Size() const {
  return py::len(m_data);
}

PyMutationList::ObjectIterator PyMutationList::Iter() const {
  return py::reinterpret_steal<ObjectIterator>(PyObject_GetIter(m_data.ptr()));
}

py::object PyMutationList::GetItem(py::object key) const {
  return m_data.attr("__getitem__")(key);
}

void PyMutationList::SetItem(py::object key, py::object value) {
  m_data.attr("__setitem__")(key, value);
  Sync();
}

void PyMutationList::DelItem(py::object key) {
  m_data.attr("__delitem__")(key);
  Sync();
}

bool PyMutationList::Contains(py::object value) const {
  int result = PySequence_Contains(m_data.ptr(), value.ptr());
  if (result < 0) {
    throw py::error_already_set{};
  }
  return result == 1;
}

bool PyMutationList::Equal(py::object value) const {
  int result = PyObject_RichCompareBool(m_data.ptr(), value.ptr(), Py_EQ);
  if (result < 0) {
    throw py::error_already_set{};
  }
  return result == 1;
}

std::string PyMutationList::Repr() const {
  return py::repr(m_data).cast<std::string>();
}

py::list PyMutationList::Copy() const {
  return py::reinterpret_borrow<py::list>(m_data.attr("copy")());
}

void PyMutationList::Append(py::object value) {
  m_data.attr("append")(value);
  Sync();
}

void PyMutationList::Extend(ObjectIterable value) {
  m_data.attr("extend")(value);
  Sync();
}

void PyMutationList::Insert(py::ssize_t index, py::object value) {
  m_data.attr("insert")(index, value);
  Sync();
}

py::object PyMutationList::Pop(std::optional<py::ssize_t> index) {
  py::object value = index ? m_data.attr("pop")(*index) : m_data.attr("pop")();
  Sync();
  return value;
}

void PyMutationList::Remove(py::object value) {
  m_data.attr("remove")(value);
  Sync();
}

void PyMutationList::Clear() {
  m_data.attr("clear")();
  Sync();
}

void PyMutationList::Reverse() {
  m_data.attr("reverse")();
  Sync();
}

void PyMutationList::Sort(std::optional<SortKey> key, bool reverse) {
  if (key) {
    m_data.attr("sort")(py::arg("key") = *key, py::arg("reverse") = reverse);
  } else {
    m_data.attr("sort")(py::arg("reverse") = reverse);
  }
  Sync();
}

PyMutationList& PyMutationList::IAdd(ObjectIterable value) {
  m_data.attr("__iadd__")(value);
  Sync();
  return *this;
}

void PyMutationList::Sync() {
  m_owner->SetCached(m_data);
}

py::object MakeMutationList(std::shared_ptr<PyTunable> owner, py::list data) {
  return py::cast(PyMutationList{std::move(owner), std::move(data)});
}

}  // namespace wpi::tunables::python
