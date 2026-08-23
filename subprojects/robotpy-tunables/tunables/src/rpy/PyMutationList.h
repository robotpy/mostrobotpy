#pragma once

#include <memory>
#include <optional>
#include <string>

#include <pybind11/pybind11.h>
#include <pybind11/typing.h>

#include "PyTunable.h"

namespace wpi::tunables::python {

class PyMutationList {
 public:
  using ObjectIterable =
      pybind11::typing::Iterable<pybind11::object>;
  using ObjectIterator =
      pybind11::typing::Iterator<pybind11::object>;
  using SortKey = pybind11::typing::Callable<
      pybind11::object(pybind11::object)>;

  PyMutationList(std::shared_ptr<PyTunable> owner, pybind11::list data);

  size_t Size() const;
  ObjectIterator Iter() const;
  pybind11::object GetItem(pybind11::object key) const;
  void SetItem(pybind11::object key, pybind11::object value);
  void DelItem(pybind11::object key);
  bool Contains(pybind11::object value) const;
  bool Equal(pybind11::object value) const;
  std::string Repr() const;
  pybind11::list Copy() const;
  void Append(pybind11::object value);
  void Extend(ObjectIterable value);
  void Insert(pybind11::ssize_t index, pybind11::object value);
  pybind11::object Pop(
      std::optional<pybind11::ssize_t> index = std::nullopt);
  void Remove(pybind11::object value);
  void Clear();
  void Reverse();
  void Sort(std::optional<SortKey> key = std::nullopt,
            bool reverse = false);
  PyMutationList& IAdd(ObjectIterable value);

 private:
  void Sync();

  std::shared_ptr<PyTunable> m_owner;
  pybind11::list m_data;
};

pybind11::object MakeMutationList(std::shared_ptr<PyTunable> owner,
                                  pybind11::list data);

}  // namespace wpi::tunables::python
