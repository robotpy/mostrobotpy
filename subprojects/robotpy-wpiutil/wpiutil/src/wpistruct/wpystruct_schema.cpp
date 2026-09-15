#include "wpystruct_schema.h"

#include <charconv>
#include <cmath>
#include <functional>
#include <limits>
#include <map>
#include <memory>
#include <span>
#include <string>
#include <utility>
#include <vector>

#include <pybind11/pybind11.h>

#include "wpi/util/struct/DynamicStruct.hpp"
#include "wpi/util/struct/SchemaParser.hpp"

namespace wpy::structs {

struct DeclarationShape {
  bool isArray = false;
  bool isBitField = false;
  bool isEnum = false;
};

class SchemaDatabaseImpl {
 public:
  std::shared_ptr<wpi::util::StructDescriptorDatabase> database =
      std::make_shared<wpi::util::StructDescriptorDatabase>();
  std::map<std::string, std::string, std::less<>> definitions;
  std::map<std::string, std::vector<DeclarationShape>, std::less<>> shapes;
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

unsigned int NormalizeBitWidth(
    const wpi::util::structparser::ParsedDeclaration& declaration) {
  if (declaration.bitWidth != 0) {
    return declaration.bitWidth;
  }

  auto type = NormalizeType(declaration.typeString);
  if (type == "int8" || type == "uint8") {
    return 8;
  }
  if (type == "int16" || type == "uint16") {
    return 16;
  }
  if (type == "int32" || type == "uint32") {
    return 32;
  }
  if (type == "int64" || type == "uint64") {
    return 64;
  }
  return 0;
}

bool DeclarationsEqual(const wpi::util::structparser::ParsedDeclaration& lhs,
                       const wpi::util::structparser::ParsedDeclaration& rhs) {
  return NormalizeType(lhs.typeString) == NormalizeType(rhs.typeString) &&
         lhs.name == rhs.name && lhs.enumValues == rhs.enumValues &&
         lhs.arraySize == rhs.arraySize &&
         NormalizeBitWidth(lhs) == NormalizeBitWidth(rhs);
}

wpi::util::structparser::ParsedSchema ParseSchema(std::string_view schema) {
  wpi::util::structparser::Parser parser{schema};
  wpi::util::structparser::ParsedSchema parsed;
  if (!parser.Parse(&parsed)) {
    throw pybind11::value_error("parse error: " + parser.GetError());
  }
  return parsed;
}

std::vector<DeclarationShape> ParseDeclarationShapes(std::string_view schema) {
  wpi::util::structparser::Lexer lexer{schema};
  std::vector<DeclarationShape> shapes;
  DeclarationShape shape;
  bool hasDeclaration = false;
  while (true) {
    auto token = lexer.Scan();
    if (token.Is(wpi::util::structparser::Token::END_OF_INPUT)) {
      if (hasDeclaration) {
        shapes.emplace_back(shape);
      }
      return shapes;
    }
    if (token.Is(wpi::util::structparser::Token::SEMICOLON)) {
      if (hasDeclaration) {
        shapes.emplace_back(shape);
        shape = {};
        hasDeclaration = false;
      }
      continue;
    }

    hasDeclaration = true;
    if (token.Is(wpi::util::structparser::Token::LEFT_BRACE)) {
      shape.isEnum = true;
    } else if (token.Is(wpi::util::structparser::Token::LEFT_BRACKET)) {
      shape.isArray = true;
    } else if (token.Is(wpi::util::structparser::Token::COLON)) {
      shape.isBitField = true;
    }
  }
}

struct PreparedDefinition {
  std::string name;
  std::string schema;
  std::vector<DeclarationShape> shapes;
};

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

void ValidateArrayExtentsForPlatform(std::string_view descriptorName,
                                     std::string_view schema) {
  wpi::util::structparser::Lexer lexer{schema};
  wpi::util::structparser::Token previous;
  for (auto token = lexer.Scan();
       !token.Is(wpi::util::structparser::Token::END_OF_INPUT);
       token = lexer.Scan()) {
    if (token.Is(wpi::util::structparser::Token::LEFT_BRACKET)) {
      auto extentToken = lexer.Scan();
      uint64_t extent = 0;
      auto result = std::from_chars(
          extentToken.text.data(),
          extentToken.text.data() + extentToken.text.size(), extent);
      if (extentToken.Is(wpi::util::structparser::Token::INTEGER) &&
          result.ec == std::errc{} &&
          extent > std::numeric_limits<size_t>::max()) {
        std::string fieldName =
            previous.Is(wpi::util::structparser::Token::IDENTIFIER)
                ? std::string{previous.text}
                : "<unknown>";
        throw pybind11::value_error(
            "unsafe schema layout for " + std::string{descriptorName} +
            ": field " + fieldName + " storage extent exceeds platform limits");
      }
      previous = extentToken;
    } else {
      previous = token;
    }
  }
}

PreparedDefinition PrepareDefinition(std::string_view name,
                                     std::string_view schema) {
  auto parsed = ParseSchema(schema);
  auto shapes = ParseDeclarationShapes(schema);
  if (shapes.size() != parsed.declarations.size()) {
    throw pybind11::value_error("failed to analyze schema declarations");
  }
  ValidateArrayExtentsForPlatform(name, schema);
  return {std::string{name}, std::string{schema}, std::move(shapes)};
}

void ValidateDescriptorLayout(const wpi::util::StructDescriptor& descriptor) {
  if (!descriptor.IsValid()) {
    return;
  }

  const size_t descriptorSize = descriptor.GetSize();
  for (const auto& field : descriptor.GetFields()) {
    const size_t fieldSize = field.GetSize();
    const size_t arraySize = field.GetArraySize();
    if (fieldSize != 0 &&
        arraySize > std::numeric_limits<size_t>::max() / fieldSize) {
      throw pybind11::value_error(
          "unsafe schema layout for " + descriptor.GetName() + ": field " +
          field.GetName() + " storage extent exceeds platform limits");
    }

    const size_t storageExtent = fieldSize * arraySize;
    const size_t offset = field.GetOffset();
    if (offset > descriptorSize || storageExtent > descriptorSize - offset) {
      throw pybind11::value_error(
          "unsafe schema layout for " + descriptor.GetName() + ": field " +
          field.GetName() + " storage extent exceeds descriptor size");
    }
  }
}

void ValidateDatabaseLayouts(
    const wpi::util::StructDescriptorDatabase& database,
    const std::map<std::string, std::string, std::less<>>& definitions,
    std::string_view candidateName) {
  for (const auto& definition : definitions) {
    const auto* descriptor = database.Find(definition.first);
    if (!descriptor) {
      throw pybind11::value_error("failed to reconstruct schema database");
    }
    ValidateDescriptorLayout(*descriptor);
  }

  const auto* candidate = database.Find(candidateName);
  if (!candidate) {
    throw pybind11::value_error("failed to reconstruct schema database");
  }
  ValidateDescriptorLayout(*candidate);
}

void ValidateCompleteDatabaseLayouts(
    const wpi::util::StructDescriptorDatabase& database,
    const std::map<std::string, std::string, std::less<>>& definitions) {
  for (const auto& definition : definitions) {
    const auto* descriptor = database.Find(definition.first);
    if (!descriptor) {
      throw pybind11::value_error("failed to reconstruct schema database");
    }
    if (!descriptor->IsValid()) {
      throw pybind11::value_error("unresolved schema definition for " +
                                  definition.first);
    }
    ValidateDescriptorLayout(*descriptor);
  }
}

std::shared_ptr<SchemaDatabaseImpl> BuildStagedDatabase(
    const std::shared_ptr<SchemaDatabaseImpl>& source, std::string_view name,
    std::string_view schema) {
  auto prepared = PrepareDefinition(name, schema);

  bool duplicate = false;
  if (auto existing = source->definitions.find(name);
      existing != source->definitions.end()) {
    if (!SchemasEqual(existing->second, schema)) {
      throw pybind11::value_error("conflicting schema for " +
                                  std::string{name});
    }
    duplicate = true;
  }

  auto staged = std::make_shared<SchemaDatabaseImpl>();
  staged->definitions = source->definitions;
  staged->shapes = source->shapes;
  std::string error;
  for (const auto& [definedName, definedSchema] : source->definitions) {
    if (!staged->database->Add(definedName, definedSchema, &error)) {
      throw pybind11::value_error("failed to reconstruct schema database: " +
                                  error);
    }
  }
  if (duplicate) {
    staged->definitions[prepared.name] = prepared.schema;
    staged->shapes[prepared.name] = std::move(prepared.shapes);
    return staged;
  }

  const auto* descriptor = staged->database->Add(name, schema, &error);
  if (!descriptor) {
    throw pybind11::value_error(error);
  }
  std::string descriptorName = descriptor->GetName();
  ValidateDatabaseLayouts(*staged->database, source->definitions,
                          descriptorName);
  staged->definitions.emplace(descriptorName, std::move(prepared.schema));
  staged->shapes.emplace(std::move(descriptorName), std::move(prepared.shapes));
  return staged;
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
[[noreturn]]
void ThrowIntegerRangeError(const wpi::util::StructFieldDescriptor& field,
                            T minimum, T maximum) {
  throw py::value_error(
      FieldError(field, "must be between " + std::to_string(minimum) + " and " +
                            std::to_string(maximum)));
}

int64_t RequireSignedInteger(const wpi::util::StructFieldDescriptor& field,
                             py::handle value, int64_t minimum,
                             int64_t maximum) {
  RequireIntegerType(field, value);
  int overflow = 0;
  int64_t converted = PyLong_AsLongLongAndOverflow(value.ptr(), &overflow);
  if (converted == -1 && PyErr_Occurred()) {
    throw py::error_already_set();
  }
  if (overflow != 0 || converted < minimum || converted > maximum) {
    ThrowIntegerRangeError(field, minimum, maximum);
  }
  return converted;
}

uint64_t RequireUnsignedInteger(const wpi::util::StructFieldDescriptor& field,
                                py::handle value, uint64_t minimum,
                                uint64_t maximum) {
  RequireIntegerType(field, value);
  uint64_t converted = PyLong_AsUnsignedLongLong(value.ptr());
  if (PyErr_Occurred()) {
    if (!PyErr_ExceptionMatches(PyExc_OverflowError)) {
      throw py::error_already_set();
    }
    PyErr_Clear();
    ThrowIntegerRangeError(field, minimum, maximum);
  }
  if (converted < minimum || converted > maximum) {
    ThrowIntegerRangeError(field, minimum, maximum);
  }
  return converted;
}

float RequireFloat32(const wpi::util::StructFieldDescriptor& field,
                     py::handle value) {
  RequireFloat(field, value);
  double converted = PyFloat_AsDouble(value.ptr());
  if (converted == -1.0 && PyErr_Occurred()) {
    throw py::error_already_set();
  }
  constexpr double kMax = std::numeric_limits<float>::max();
  if (std::isfinite(converted) && (converted < -kMax || converted > kMax)) {
    throw py::value_error(FieldError(field, "must be within float32 range"));
  }
  return static_cast<float>(converted);
}

py::sequence RequireArray(const wpi::util::StructFieldDescriptor& field,
                          py::handle value) {
  if (!PySequence_Check(value.ptr()) || PyUnicode_Check(value.ptr())) {
    throw py::type_error(FieldError(field, "must be a sequence"));
  }
  auto sequence = py::reinterpret_borrow<py::sequence>(value);
  if (sequence.size() != field.GetArraySize()) {
    throw py::value_error(FieldError(
        field,
        "must contain " + std::to_string(field.GetArraySize()) + " values"));
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
    throw py::value_error(
        FieldError(field, "must be " + std::to_string(expected) + " bytes"));
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
      output.SetIntField(&field,
                         RequireSignedInteger(field, value, field.GetIntMin(),
                                              field.GetIntMax()),
                         index);
      return;
    case StructFieldType::UINT8:
    case StructFieldType::UINT16:
    case StructFieldType::UINT32:
    case StructFieldType::UINT64:
      output.SetUintField(
          &field,
          RequireUnsignedInteger(field, value, field.GetUintMin(),
                                 field.GetUintMax()),
          index);
      return;
    case StructFieldType::FLOAT:
      output.SetFloatField(&field, RequireFloat32(field, value), index);
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
    if (!output.SetStringField(&field, {data, static_cast<size_t>(size)})) {
      throw py::value_error(FieldError(
          field,
          "must fit in " + std::to_string(field.GetArraySize()) + " bytes"));
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
  if (auto definition = m_impl->definitions.find(m_name);
      definition != m_impl->definitions.end()) {
    return definition->second;
  }
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
  const auto& nativeFields = descriptor.GetFields();
  const auto shapeIt = m_impl->shapes.find(m_name);
  if (shapeIt == m_impl->shapes.end()) {
    if (nativeFields.empty()) {
      return {};
    }
    throw pybind11::value_error(
        "schema declaration metadata is unavailable for " + m_name);
  }
  const auto& shapes = shapeIt->second;
  if (shapes.size() != nativeFields.size()) {
    throw pybind11::value_error(
        "schema declaration metadata is inconsistent for " + m_name);
  }

  std::vector<SchemaFieldDescriptor> fields;
  fields.reserve(nativeFields.size());
  for (size_t index = 0; index < nativeFields.size(); ++index) {
    const auto& field = nativeFields[index];
    const auto& shape = shapes[index];
    std::optional<std::string> structName;
    if (const auto* nested = field.GetStruct()) {
      structName = nested->GetName();
    }
    fields.emplace_back(
        field.GetName(), FieldTypeName(field), field.GetSize(),
        field.GetOffset(), field.GetArraySize(), field.GetBitWidth(),
        field.GetBitShift(), field.GetBitMask(), field.GetEnumValues(),
        std::move(structName), shape.isArray, shape.isBitField, shape.isEnum);
  }
  return fields;
}

SchemaDatabase::SchemaDatabase()
    : m_impl{std::make_shared<SchemaDatabaseImpl>()} {}

SchemaDescriptor SchemaDatabase::Add(std::string_view name,
                                     std::string_view schema) {
  if (auto existing = m_impl->definitions.find(name);
      existing != m_impl->definitions.end()) {
    ParseSchema(schema);
    ValidateArrayExtentsForPlatform(name, schema);
    if (!SchemasEqual(existing->second, schema)) {
      throw pybind11::value_error("conflicting schema for " +
                                  std::string{name});
    }
    return SchemaDescriptor{m_impl, std::string{name}};
  }

  auto staged = BuildStagedDatabase(m_impl, name, schema);
  if (staged != m_impl) {
    m_impl->database = std::move(staged->database);
    m_impl->definitions = std::move(staged->definitions);
    m_impl->shapes = std::move(staged->shapes);
  }
  return SchemaDescriptor{m_impl, std::string{name}};
}

void SchemaDatabase::AddAll(
    const std::vector<std::pair<std::string, std::string>>& definitions) {
  if (definitions.empty()) {
    return;
  }

  std::vector<PreparedDefinition> prepared;
  prepared.reserve(definitions.size());
  for (const auto& [name, schema] : definitions) {
    prepared.emplace_back(PrepareDefinition(name, schema));
  }

  auto staged = std::make_shared<SchemaDatabaseImpl>();
  staged->definitions = m_impl->definitions;
  staged->shapes = m_impl->shapes;
  std::string error;
  for (const auto& [name, schema] : m_impl->definitions) {
    if (!staged->database->Add(name, schema, &error)) {
      throw pybind11::value_error("failed to reconstruct schema database: " +
                                  error);
    }
  }

  for (auto& definition : prepared) {
    if (auto existing = staged->definitions.find(definition.name);
        existing != staged->definitions.end()) {
      if (!SchemasEqual(existing->second, definition.schema)) {
        throw pybind11::value_error("conflicting schema for " +
                                    definition.name);
      }
      continue;
    }

    const auto* descriptor =
        staged->database->Add(definition.name, definition.schema, &error);
    if (!descriptor) {
      throw pybind11::value_error(error);
    }
    std::string descriptorName = descriptor->GetName();
    staged->definitions.emplace(descriptorName, std::move(definition.schema));
    staged->shapes.emplace(std::move(descriptorName),
                           std::move(definition.shapes));
  }

  ValidateCompleteDatabaseLayouts(*staged->database, staged->definitions);
  m_impl->database = std::move(staged->database);
  m_impl->definitions = std::move(staged->definitions);
  m_impl->shapes = std::move(staged->shapes);
}

SchemaDatabase SchemaDatabase::Stage(std::string_view name,
                                     std::string_view schema) const {
  SchemaDatabase staged;
  staged.m_impl = BuildStagedDatabase(m_impl, name, schema);
  return staged;
}

std::optional<SchemaDescriptor> SchemaDatabase::Find(
    std::string_view name) const {
  const auto* descriptor = m_impl->database->Find(name);
  if (!descriptor) {
    return std::nullopt;
  }
  return SchemaDescriptor{m_impl, descriptor->GetName()};
}

py::bytes PackSchema(const SchemaDescriptor& desc, const py::sequence& values) {
  auto database = desc.m_impl->database;
  const auto& descriptor = ResolveDescriptor(database, desc.m_name);
  if (!descriptor.IsValid()) {
    throw py::value_error("descriptor " + desc.m_name + " is not valid");
  }

  const auto& fields = descriptor.GetFields();
  if (values.size() != fields.size()) {
    throw py::value_error("expected " + std::to_string(fields.size()) +
                          " fields, got " + std::to_string(values.size()));
  }

  std::vector<uint8_t> data(descriptor.GetSize(), 0);
  wpi::util::MutableDynamicStruct output{&descriptor, data};
  for (size_t i = 0; i < fields.size(); ++i) {
    PackField(output, fields[i], values[static_cast<py::ssize_t>(i)]);
  }
  return {reinterpret_cast<const char*>(data.data()), data.size()};
}

py::tuple UnpackSchema(const SchemaDescriptor& desc, const py::buffer& buffer) {
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

  std::span<const uint8_t> data{reinterpret_cast<const uint8_t*>(request.ptr),
                                descriptor.GetSize()};
  wpi::util::DynamicStruct input{&descriptor, data};
  const auto& fields = descriptor.GetFields();
  py::tuple values{static_cast<py::ssize_t>(fields.size())};
  for (size_t i = 0; i < fields.size(); ++i) {
    values[static_cast<py::ssize_t>(i)] = UnpackField(input, fields[i]);
  }
  return values;
}

}  // namespace wpy::structs
