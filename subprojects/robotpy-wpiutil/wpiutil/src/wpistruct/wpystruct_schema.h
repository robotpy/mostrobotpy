#pragma once

#include <cstddef>
#include <memory>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <pybind11/pybind11.h>

namespace py = pybind11;

namespace wpy::structs {

class SchemaDatabaseImpl;

class SchemaDescriptor {
 public:
  bool IsValid() const;
  size_t GetSize() const;

 private:
  friend class SchemaDatabase;
  friend py::bytes PackSchema(const SchemaDescriptor& desc,
                              const py::sequence& values);
  friend py::tuple UnpackSchema(const SchemaDescriptor& desc,
                                const py::buffer& buffer);
  SchemaDescriptor(std::shared_ptr<SchemaDatabaseImpl> impl, std::string name);
  std::shared_ptr<SchemaDatabaseImpl> m_impl;
  std::string m_name;
};

class SchemaDatabase {
 public:
  SchemaDatabase();
  SchemaDescriptor Add(std::string_view name, std::string_view schema);
  void AddAll(
      const std::vector<std::pair<std::string, std::string>>& definitions);

 private:
  std::shared_ptr<SchemaDatabaseImpl> m_impl;
};

py::bytes PackSchema(const SchemaDescriptor& desc, const py::sequence& values);
py::tuple UnpackSchema(const SchemaDescriptor& desc, const py::buffer& buffer);

}  // namespace wpy::structs
