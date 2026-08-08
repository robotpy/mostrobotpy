#include "wpystruct_schema.h"

#include <map>
#include <span>
#include <string>

#include <pybind11/pybind11.h>

#include "wpi/util/struct/DynamicStruct.hpp"
#include "wpi/util/struct/SchemaParser.hpp"

namespace wpy::structs {

class SchemaDatabaseImpl {
 public:
  std::shared_ptr<wpi::util::StructDescriptorDatabase> database =
      std::make_shared<wpi::util::StructDescriptorDatabase>();
  std::map<std::string, std::string, std::less<>> definitions;
};

namespace {

const wpi::util::StructDescriptor& ResolveDescriptor(
    const std::shared_ptr<wpi::util::StructDescriptorDatabase>& database,
    std::string_view name) {
  const auto* descriptor = database->Find(name);
  if (!descriptor) {
    throw pybind11::value_error("descriptor " + std::string{name} +
                               " does not exist");
  }
  return *descriptor;
}

const wpi::util::StructDescriptor& ResolveDescriptor(
    const std::shared_ptr<SchemaDatabaseImpl>& impl, std::string_view name) {
  return ResolveDescriptor(impl->database, name);
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

std::string FieldError(const wpi::util::StructFieldDescriptor& field,
                       std::string_view message) {
  return "field " + field.GetName() + " " + std::string{message};
}

void RequireBool(const wpi::util::StructFieldDescriptor& field,
                 py::handle value) {
  if (!PyBool_Check(value.ptr())) {
    throw py::type_error(FieldError(field, "must be a bool"));
  }
}

void RequireFloat(const wpi::util::StructFieldDescriptor& field,
                  py::handle value) {
  if (!PyFloat_Check(value.ptr())) {
    throw py::type_error(FieldError(field, "must be a float"));
  }
}

void RequireIntegerType(const wpi::util::StructFieldDescriptor& field,
                        py::handle value) {
  if (!PyLong_Check(value.ptr()) || PyBool_Check(value.ptr())) {
    throw py::type_error(FieldError(field, "must be an integer"));
  }
}

template <typename T>
void RequireIntegerRange(const wpi::util::StructFieldDescriptor& field,
                         py::handle value, T minimum, T maximum) {
  RequireIntegerType(field, value);
  py::int_ pyMinimum{minimum};
  py::int_ pyMaximum{maximum};
  int below = PyObject_RichCompareBool(value.ptr(), pyMinimum.ptr(), Py_LT);
  if (below < 0) {
    throw py::error_already_set();
  }
  int above = PyObject_RichCompareBool(value.ptr(), pyMaximum.ptr(), Py_GT);
  if (above < 0) {
    throw py::error_already_set();
  }
  if (below || above) {
    throw py::value_error(FieldError(
        field, "must be between " + std::to_string(minimum) + " and " +
                   std::to_string(maximum)));
  }
}

py::sequence RequireArray(const wpi::util::StructFieldDescriptor& field,
                          py::handle value) {
  if (!PySequence_Check(value.ptr()) || PyUnicode_Check(value.ptr())) {
    throw py::type_error(FieldError(field, "must be a sequence"));
  }
  auto sequence = py::reinterpret_borrow<py::sequence>(value);
  if (sequence.size() != field.GetArraySize()) {
    throw py::value_error(
        FieldError(field, "must contain " +
                              std::to_string(field.GetArraySize()) +
                              " values"));
  }
  return sequence;
}

std::span<const uint8_t> RequireNestedBytes(
    const wpi::util::StructFieldDescriptor& field, py::handle value) {
  if (!PyBytes_Check(value.ptr())) {
    throw py::type_error(FieldError(field, "must be bytes"));
  }
  char* data;
  Py_ssize_t size;
  if (PyBytes_AsStringAndSize(value.ptr(), &data, &size) != 0) {
    throw py::error_already_set();
  }
  size_t expected = field.GetStruct()->GetSize();
  if (size != static_cast<Py_ssize_t>(expected)) {
    throw py::value_error(FieldError(
        field, "must be " + std::to_string(expected) + " bytes"));
  }
  return {reinterpret_cast<const uint8_t*>(data), expected};
}

void PackElement(wpi::util::MutableDynamicStruct& output,
                 const wpi::util::StructFieldDescriptor& field,
                 py::handle value, size_t index) {
  using wpi::util::StructFieldType;

  switch (field.GetType()) {
    case StructFieldType::BOOL:
      RequireBool(field, value);
      output.SetBoolField(&field, value.ptr() == Py_True, index);
      return;
    case StructFieldType::INT8:
    case StructFieldType::INT16:
    case StructFieldType::INT32:
    case StructFieldType::INT64:
      RequireIntegerRange(field, value, field.GetIntMin(), field.GetIntMax());
      output.SetIntField(&field, py::cast<int64_t>(value), index);
      return;
    case StructFieldType::UINT8:
    case StructFieldType::UINT16:
    case StructFieldType::UINT32:
    case StructFieldType::UINT64:
      RequireIntegerRange(field, value, field.GetUintMin(),
                          field.GetUintMax());
      output.SetUintField(&field, py::cast<uint64_t>(value), index);
      return;
    case StructFieldType::FLOAT:
      RequireFloat(field, value);
      output.SetFloatField(&field, py::cast<float>(value), index);
      return;
    case StructFieldType::DOUBLE:
      RequireFloat(field, value);
      output.SetDoubleField(&field, py::cast<double>(value), index);
      return;
    case StructFieldType::STRUCT: {
      auto data = RequireNestedBytes(field, value);
      wpi::util::DynamicStruct nested{field.GetStruct(), data};
      output.SetStructField(&field, nested, index);
      return;
    }
    case StructFieldType::CHAR:
      throw py::type_error(FieldError(field, "must be a string"));
  }
}

void PackField(wpi::util::MutableDynamicStruct& output,
               const wpi::util::StructFieldDescriptor& field,
               py::handle value) {
  if (field.GetType() == wpi::util::StructFieldType::CHAR) {
    if (!PyUnicode_Check(value.ptr())) {
      throw py::type_error(FieldError(field, "must be a string"));
    }
    Py_ssize_t size;
    const char* data = PyUnicode_AsUTF8AndSize(value.ptr(), &size);
    if (!data) {
      throw py::error_already_set();
    }
    if (!output.SetStringField(&field,
                               {data, static_cast<size_t>(size)})) {
      throw py::value_error(
          FieldError(field, "must fit in " +
                                std::to_string(field.GetArraySize()) +
                                " bytes"));
    }
    return;
  }

  if (field.IsArray()) {
    auto sequence = RequireArray(field, value);
    for (size_t i = 0; i < field.GetArraySize(); ++i) {
      PackElement(output, field, sequence[static_cast<py::ssize_t>(i)], i);
    }
    return;
  }

  PackElement(output, field, value, 0);
}

int64_t UnpackSignedElement(const wpi::util::DynamicStruct& input,
                            const wpi::util::StructFieldDescriptor& field,
                            size_t index) {
  uint64_t raw = static_cast<uint64_t>(input.GetIntField(&field, index));
  unsigned int width = field.GetBitWidth();
  if (width < 64 && (raw & (uint64_t{1} << (width - 1))) != 0) {
    raw |= ~field.GetBitMask();
  }
  return static_cast<int64_t>(raw);
}

py::object UnpackElement(const wpi::util::DynamicStruct& input,
                         const wpi::util::StructFieldDescriptor& field,
                         size_t index) {
  using wpi::util::StructFieldType;

  switch (field.GetType()) {
    case StructFieldType::BOOL:
      return py::bool_{input.GetBoolField(&field, index)};
    case StructFieldType::INT8:
    case StructFieldType::INT16:
    case StructFieldType::INT32:
    case StructFieldType::INT64:
      return py::int_{UnpackSignedElement(input, field, index)};
    case StructFieldType::UINT8:
    case StructFieldType::UINT16:
    case StructFieldType::UINT32:
    case StructFieldType::UINT64:
      return py::int_{input.GetUintField(&field, index)};
    case StructFieldType::FLOAT:
      return py::float_{input.GetFloatField(&field, index)};
    case StructFieldType::DOUBLE:
      return py::float_{input.GetDoubleField(&field, index)};
    case StructFieldType::STRUCT: {
      auto data = input.GetStructField(&field, index).GetData();
      return py::bytes{reinterpret_cast<const char*>(data.data()),
                       field.GetStruct()->GetSize()};
    }
    case StructFieldType::CHAR:
      break;
  }
  throw py::type_error(FieldError(field, "has an unsupported type"));
}

py::object UnpackField(const wpi::util::DynamicStruct& input,
                       const wpi::util::StructFieldDescriptor& field) {
  if (field.GetType() == wpi::util::StructFieldType::CHAR) {
    auto value = input.GetStringField(&field);
    PyObject* decoded =
        PyUnicode_DecodeUTF8(value.data(), value.size(), "strict");
    if (!decoded) {
      throw py::error_already_set();
    }
    return py::reinterpret_steal<py::str>(decoded);
  }

  if (field.IsArray()) {
    py::tuple values{static_cast<py::ssize_t>(field.GetArraySize())};
    for (size_t i = 0; i < field.GetArraySize(); ++i) {
      values[static_cast<py::ssize_t>(i)] = UnpackElement(input, field, i);
    }
    return values;
  }

  return UnpackElement(input, field, 0);
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

  auto stagedDatabase =
      std::make_shared<wpi::util::StructDescriptorDatabase>();
  std::string error;
  for (const auto& [definedName, definedSchema] : m_impl->definitions) {
    if (!stagedDatabase->Add(definedName, definedSchema, &error)) {
      throw pybind11::value_error("failed to reconstruct schema database: " +
                                  error);
    }
  }

  const auto* descriptor = stagedDatabase->Add(name, schema, &error);
  if (!descriptor) {
    throw pybind11::value_error(error);
  }
  std::string descriptorName = descriptor->GetName();
  std::string descriptorSchema = descriptor->GetSchema();
  m_impl->definitions.emplace(descriptorName, std::move(descriptorSchema));
  m_impl->database = std::move(stagedDatabase);
  return SchemaDescriptor{m_impl, std::move(descriptorName)};
}

std::optional<SchemaDescriptor> SchemaDatabase::Find(
    std::string_view name) const {
  const auto* descriptor = m_impl->database->Find(name);
  if (!descriptor) {
    return std::nullopt;
  }
  return SchemaDescriptor{m_impl, descriptor->GetName()};
}

py::bytes PackSchema(const SchemaDescriptor& desc,
                     const py::sequence& values) {
  auto database = desc.m_impl->database;
  const auto& descriptor = ResolveDescriptor(database, desc.m_name);
  if (!descriptor.IsValid()) {
    throw py::value_error("descriptor " + desc.m_name + " is not valid");
  }

  const auto& fields = descriptor.GetFields();
  if (values.size() != fields.size()) {
    throw py::value_error("expected " + std::to_string(fields.size()) +
                          " fields, got " +
                          std::to_string(values.size()));
  }

  std::vector<uint8_t> data(descriptor.GetSize(), 0);
  wpi::util::MutableDynamicStruct output{&descriptor, data};
  for (size_t i = 0; i < fields.size(); ++i) {
    PackField(output, fields[i], values[static_cast<py::ssize_t>(i)]);
  }
  return {reinterpret_cast<const char*>(data.data()), data.size()};
}

py::tuple UnpackSchema(const SchemaDescriptor& desc,
                       const py::buffer& buffer) {
  auto database = desc.m_impl->database;
  const auto& descriptor = ResolveDescriptor(database, desc.m_name);
  if (!descriptor.IsValid()) {
    throw py::value_error("descriptor " + desc.m_name + " is not valid");
  }

  auto request = buffer.request();
  if (request.itemsize != 1) {
    throw py::value_error("buffer must only contain bytes");
  }
  if (request.ndim != 1) {
    throw py::value_error("buffer must only have a single dimension");
  }
  if (request.size != static_cast<py::ssize_t>(descriptor.GetSize())) {
    throw py::value_error("buffer must be " +
                          std::to_string(descriptor.GetSize()) + " bytes");
  }
  if (request.strides[0] != 1) {
    throw py::value_error("buffer must be contiguous");
  }

  std::span<const uint8_t> data{
      reinterpret_cast<const uint8_t*>(request.ptr), descriptor.GetSize()};
  wpi::util::DynamicStruct input{&descriptor, data};
  const auto& fields = descriptor.GetFields();
  py::tuple values{static_cast<py::ssize_t>(fields.size())};
  for (size_t i = 0; i < fields.size(); ++i) {
    values[static_cast<py::ssize_t>(i)] = UnpackField(input, fields[i]);
  }
  return values;
}

}  // namespace wpy::structs
