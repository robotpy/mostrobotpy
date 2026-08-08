#include "wpystruct_schema.h"

#include <map>
#include <string>

#include <pybind11/pybind11.h>

#include "wpi/util/struct/DynamicStruct.hpp"
#include "wpi/util/struct/SchemaParser.hpp"

namespace wpy::structs {

class SchemaDatabaseImpl {
 public:
  wpi::util::StructDescriptorDatabase database;
  std::map<std::string, std::string, std::less<>> definitions;
};

namespace {

const wpi::util::StructDescriptor& ResolveDescriptor(
    const std::shared_ptr<SchemaDatabaseImpl>& impl, std::string_view name) {
  const auto* descriptor = impl->database.Find(name);
  if (!descriptor) {
    throw pybind11::value_error("descriptor " + std::string{name} +
                               " does not exist");
  }
  return *descriptor;
}

std::string_view NormalizeType(std::string_view type) {
  if (type == "float32") {
    return "float";
  }
  if (type == "float64") {
    return "double";
  }
  return type;
}

bool DeclarationsEqual(
    const wpi::util::structparser::ParsedDeclaration& lhs,
    const wpi::util::structparser::ParsedDeclaration& rhs) {
  return NormalizeType(lhs.typeString) == NormalizeType(rhs.typeString) &&
         lhs.name == rhs.name && lhs.enumValues == rhs.enumValues &&
         lhs.arraySize == rhs.arraySize && lhs.bitWidth == rhs.bitWidth;
}

wpi::util::structparser::ParsedSchema ParseSchema(std::string_view schema) {
  wpi::util::structparser::Parser parser{schema};
  wpi::util::structparser::ParsedSchema parsed;
  if (!parser.Parse(&parsed)) {
    throw pybind11::value_error("parse error: " + parser.GetError());
  }
  return parsed;
}

bool SchemasEqual(std::string_view lhs, std::string_view rhs) {
  auto parsedLhs = ParseSchema(lhs);
  auto parsedRhs = ParseSchema(rhs);
  if (parsedLhs.declarations.size() != parsedRhs.declarations.size()) {
    return false;
  }
  for (size_t i = 0; i < parsedLhs.declarations.size(); ++i) {
    if (!DeclarationsEqual(parsedLhs.declarations[i],
                           parsedRhs.declarations[i])) {
      return false;
    }
  }
  return true;
}

std::string FieldTypeName(const wpi::util::StructFieldDescriptor& field) {
  using wpi::util::StructFieldType;

  switch (field.GetType()) {
    case StructFieldType::BOOL:
      return "bool";
    case StructFieldType::CHAR:
      return "char";
    case StructFieldType::INT8:
      return "int8";
    case StructFieldType::INT16:
      return "int16";
    case StructFieldType::INT32:
      return "int32";
    case StructFieldType::INT64:
      return "int64";
    case StructFieldType::UINT8:
      return "uint8";
    case StructFieldType::UINT16:
      return "uint16";
    case StructFieldType::UINT32:
      return "uint32";
    case StructFieldType::UINT64:
      return "uint64";
    case StructFieldType::FLOAT:
      return "float";
    case StructFieldType::DOUBLE:
      return "double";
    case StructFieldType::STRUCT:
      return field.GetStruct()->GetName();
  }
  return {};
}

}  // namespace

SchemaDescriptor::SchemaDescriptor(std::shared_ptr<SchemaDatabaseImpl> impl,
                                   std::string name)
    : m_impl{std::move(impl)}, m_name{std::move(name)} {}

std::string SchemaDescriptor::GetName() const {
  return ResolveDescriptor(m_impl, m_name).GetName();
}

std::string SchemaDescriptor::GetSchema() const {
  return ResolveDescriptor(m_impl, m_name).GetSchema();
}

bool SchemaDescriptor::IsValid() const {
  return ResolveDescriptor(m_impl, m_name).IsValid();
}

size_t SchemaDescriptor::GetSize() const {
  const auto& descriptor = ResolveDescriptor(m_impl, m_name);
  if (!descriptor.IsValid()) {
    throw pybind11::value_error("descriptor " + m_name + " is not valid");
  }
  return descriptor.GetSize();
}

std::vector<SchemaFieldDescriptor> SchemaDescriptor::GetFields() const {
  const auto& descriptor = ResolveDescriptor(m_impl, m_name);
  std::vector<SchemaFieldDescriptor> fields;
  fields.reserve(descriptor.GetFields().size());
  for (const auto& field : descriptor.GetFields()) {
    std::optional<std::string> structName;
    if (const auto* nested = field.GetStruct()) {
      structName = nested->GetName();
    }
    fields.emplace_back(
        field.GetName(), FieldTypeName(field), field.GetSize(),
        field.GetOffset(), field.GetArraySize(), field.GetBitWidth(),
        field.GetBitShift(), field.GetBitMask(), field.GetEnumValues(),
        std::move(structName));
  }
  return fields;
}

SchemaDatabase::SchemaDatabase() : m_impl{std::make_shared<SchemaDatabaseImpl>()} {}

SchemaDescriptor SchemaDatabase::Add(std::string_view name,
                                     std::string_view schema) {
  if (auto existing = m_impl->definitions.find(name);
      existing != m_impl->definitions.end()) {
    if (!SchemasEqual(existing->second, schema)) {
      throw pybind11::value_error("conflicting schema for " +
                                  std::string{name});
    }
    return SchemaDescriptor{m_impl, std::string{name}};
  }

  std::string error;
  const auto* descriptor = m_impl->database.Add(name, schema, &error);
  if (!descriptor) {
    throw pybind11::value_error(error);
  }
  m_impl->definitions.emplace(descriptor->GetName(), descriptor->GetSchema());
  return SchemaDescriptor{m_impl, descriptor->GetName()};
}

std::optional<SchemaDescriptor> SchemaDatabase::Find(
    std::string_view name) const {
  const auto* descriptor = m_impl->database.Find(name);
  if (!descriptor) {
    return std::nullopt;
  }
  return SchemaDescriptor{m_impl, descriptor->GetName()};
}

}  // namespace wpy::structs
