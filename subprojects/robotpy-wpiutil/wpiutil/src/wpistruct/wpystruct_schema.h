#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include <pybind11/pybind11.h>

namespace py = pybind11;

namespace wpy::structs {

class SchemaDatabaseImpl;

struct SchemaFieldDescriptor {
  std::string name;
  std::string type;
  size_t size;
  size_t offset;
  size_t arraySize;
  unsigned int bitWidth;
  unsigned int bitShift;
  uint64_t bitMask;
  std::vector<std::pair<std::string, int64_t>> enumValues;
  std::optional<std::string> structName;
  bool isArray;
  bool isBitField;
  bool isEnum;
};

class SchemaDescriptor {
 public:
  std::string GetName() const;
  std::string GetSchema() const;
  bool IsValid() const;
  size_t GetSize() const;
  std::vector<SchemaFieldDescriptor> GetFields() const;

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
  SchemaDatabase Stage(std::string_view name, std::string_view schema) const;
  std::optional<SchemaDescriptor> Find(std::string_view name) const;

 private:
  std::shared_ptr<SchemaDatabaseImpl> m_impl;
};

py::bytes PackSchema(const SchemaDescriptor& desc, const py::sequence& values);
py::tuple UnpackSchema(const SchemaDescriptor& desc, const py::buffer& buffer);

}  // namespace wpy::structs
