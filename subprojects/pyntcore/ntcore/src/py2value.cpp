
#include "py2value.h"

#include <vector>

// type casters
#include <pybind11/stl.h>
#include <wpi_span_type_caster.h>



namespace pyntcore {

const char * nttype2str(NT_Type type) {
  switch (type) {
  case NT_BOOLEAN:
    return "bool";
  case NT_DOUBLE:
    return "double";
  case NT_STRING:
    return "string";
  case NT_RAW:
    return "raw";
  case NT_BOOLEAN_ARRAY:
    return "bool[]";
  case NT_DOUBLE_ARRAY:
    return "double[]";
  case NT_STRING_ARRAY:
    return "string[]";
  case NT_INTEGER:
    return "int";
  case NT_FLOAT:
    return "float";
  case NT_INTEGER_ARRAY:
    return "int[]";
  case NT_FLOAT_ARRAY:
    return "float[]";
  default:
    return "invalid";
  }
}


py::object ntvalue2py(const nt::Value &ntvalue) {
  auto &v = ntvalue.value();
  switch (v.type) {
  case NT_BOOLEAN:
    return py::bool_(v.data.v_boolean);

  case NT_DOUBLE:
    return py::float_(v.data.v_double);

  case NT_STRING:
    return py::str(v.data.v_string.str, v.data.v_string.len);

  case NT_RAW:
    return py::bytes(v.data.v_string.str, v.data.v_string.len);

  case NT_BOOLEAN_ARRAY: {
    py::list l(v.data.arr_boolean.size);
    for (size_t i = 0; i < v.data.arr_boolean.size; i++) {
      auto b = py::bool_(v.data.arr_boolean.arr[i]);
      PyList_SET_ITEM(l.ptr(), i, b.release().ptr());
    }
    return std::move(l);
  }

  case NT_DOUBLE_ARRAY: {
    py::list l(v.data.arr_double.size);
    for (size_t i = 0; i < v.data.arr_double.size; i++) {
      auto d = py::float_(v.data.arr_double.arr[i]);
      PyList_SET_ITEM(l.ptr(), i, d.release().ptr());
    }
    return std::move(l);
  }
  
  case NT_STRING_ARRAY: {
    return py::cast(ntvalue.GetStringArray());
  }

  case NT_INTEGER: {
    return py::int_(v.data.v_int);
  }

  case NT_FLOAT: {
    return py::float_(v.data.v_float);
  }

  case NT_INTEGER_ARRAY: {
    py::list l(v.data.arr_int.size);
    for (size_t i = 0; i < v.data.arr_int.size; i++) {
      auto d = py::int_(v.data.arr_int.arr[i]);
      PyList_SET_ITEM(l.ptr(), i, d.release().ptr());
    }
    return std::move(l);
  }

  case NT_FLOAT_ARRAY: {
    py::list l(v.data.arr_float.size);
    for (size_t i = 0; i < v.data.arr_float.size; i++) {
      auto d = py::float_(v.data.arr_float.arr[i]);
      PyList_SET_ITEM(l.ptr(), i, d.release().ptr());
    }
    return std::move(l);
  }

  default:
    return py::none();
  }
}

nt::Value py2ntvalue(py::handle h) {
  if (py::isinstance<py::bool_>(h)) {
    return nt::Value::MakeBoolean(h.cast<bool>());
  } else if (py::isinstance<py::float_>(h)) {
    return nt::Value::MakeDouble(h.cast<double>());
  } else if (py::isinstance<py::int_>(h)) {
    return nt::Value::MakeInteger(h.cast<int64_t>());
  } else if (py::isinstance<py::str>(h)) {
    return nt::Value::MakeString(h.cast<std::string>());
  } else if (py::isinstance<py::bytes>(h)) {
    return nt::Value::MakeRaw(h.cast<std::span<const uint8_t>>());
  } else if (py::isinstance<py::none>(h)) {
    throw py::value_error("Cannot put None into NetworkTable");
  }

  auto seq = h.cast<py::sequence>();
  if (seq.size() == 0) {
    throw py::type_error("If you use a list here, cannot be empty");
  }
  // check the first item
  auto i1 = seq[0];
  if (py::isinstance<py::bool_>(i1)) {
    auto v = h.cast<std::vector<int>>();
    return nt::Value::MakeBooleanArray(v);
  } else if (py::isinstance<py::float_>(i1)) {
    auto v = h.cast<std::vector<double>>();
    return nt::Value::MakeDoubleArray(v);
  } else if (py::isinstance<py::int_>(i1)) {
    auto v = h.cast<std::vector<int64_t>>();
    return nt::Value::MakeIntegerArray(v);
  } else if (py::isinstance<py::str>(i1)) {
    auto v = h.cast<std::vector<std::string>>();
    return nt::Value::MakeStringArray(v);
  } else {
    throw py::value_error("Can only put bool/int/float/str/bytes or lists/tuples of them");
  }
}

py::cpp_function valueFactoryByType(nt::NetworkTableType type) {
  switch (type) {
  case nt::NetworkTableType::kBoolean:
    return py::cpp_function([](bool v) { return nt::Value::MakeBoolean(v); });
  case nt::NetworkTableType::kDouble:
    return py::cpp_function([](double v) { return nt::Value::MakeDouble(v); });
  case nt::NetworkTableType::kString:
    return py::cpp_function([](std::string_view v) { return nt::Value::MakeString(v); });
  case nt::NetworkTableType::kRaw:
    return py::cpp_function([](std::string_view v) { return nt::Value::MakeString(v); });
  case nt::NetworkTableType::kBooleanArray: 
    return py::cpp_function([](std::span<const bool> v) { return nt::Value::MakeBooleanArray(v); });
  case nt::NetworkTableType::kDoubleArray: 
    return py::cpp_function([](std::span<const double> v) { return nt::Value::MakeDoubleArray(v); });
  case nt::NetworkTableType::kStringArray:
    return py::cpp_function([](std::vector<std::string> v) { return nt::Value::MakeStringArray(std::move(v)); });
  case nt::NetworkTableType::kInteger:
    return py::cpp_function([](int64_t v) { return nt::Value::MakeInteger(v); });
  case nt::NetworkTableType::kFloat:
    return py::cpp_function([](float v) { return nt::Value::MakeFloat(v); });
  case nt::NetworkTableType::kIntegerArray:
    return py::cpp_function([](std::span<const int64_t> v) { return nt::Value::MakeIntegerArray(v); });
  case nt::NetworkTableType::kFloatArray:
    return py::cpp_function([](std::span<const float> v) { return nt::Value::MakeFloatArray(v); });
  default:
    throw py::type_error("empty nt value");
  }
}

}
