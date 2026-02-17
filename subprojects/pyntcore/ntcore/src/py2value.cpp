
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


nb::object ntvalue2py(const nt::Value &ntvalue) {
  auto &v = ntvalue.value();
  switch (v.type) {
  case NT_BOOLEAN:
    return nb::bool_(v.data.v_boolean);

  case NT_DOUBLE:
    return nb::float_(v.data.v_double);

  case NT_STRING:
    return nb::str(v.data.v_string.str, v.data.v_string.len);

  case NT_RAW:
    return nb::bytes((const char *)v.data.v_raw.data, v.data.v_raw.size);

  case NT_BOOLEAN_ARRAY: {
    nb::list l(v.data.arr_boolean.size);
    for (size_t i = 0; i < v.data.arr_boolean.size; i++) {
      auto b = nb::bool_(v.data.arr_boolean.arr[i]);
      PyList_SET_ITEM(l.ptr(), i, b.release().ptr());
    }
    return std::move(l);
  }

  case NT_DOUBLE_ARRAY: {
    nb::list l(v.data.arr_double.size);
    for (size_t i = 0; i < v.data.arr_double.size; i++) {
      auto d = nb::float_(v.data.arr_double.arr[i]);
      PyList_SET_ITEM(l.ptr(), i, d.release().ptr());
    }
    return std::move(l);
  }
  
  case NT_STRING_ARRAY: {
    return nb::cast(ntvalue.GetStringArray());
  }

  case NT_INTEGER: {
    return nb::int_(v.data.v_int);
  }

  case NT_FLOAT: {
    return nb::float_(v.data.v_float);
  }

  case NT_INTEGER_ARRAY: {
    nb::list l(v.data.arr_int.size);
    for (size_t i = 0; i < v.data.arr_int.size; i++) {
      auto d = nb::int_(v.data.arr_int.arr[i]);
      PyList_SET_ITEM(l.ptr(), i, d.release().ptr());
    }
    return std::move(l);
  }

  case NT_FLOAT_ARRAY: {
    nb::list l(v.data.arr_float.size);
    for (size_t i = 0; i < v.data.arr_float.size; i++) {
      auto d = nb::float_(v.data.arr_float.arr[i]);
      PyList_SET_ITEM(l.ptr(), i, d.release().ptr());
    }
    return std::move(l);
  }

  default:
    return nb::none();
  }
}

nt::Value py2ntvalue(nb::handle h) {
  if (nb::isinstance<nb::bool_>(h)) {
    return nt::Value::MakeBoolean(h.cast<bool>());
  } else if (nb::isinstance<nb::float_>(h)) {
    return nt::Value::MakeDouble(h.cast<double>());
  } else if (nb::isinstance<nb::int_>(h)) {
    return nt::Value::MakeInteger(h.cast<int64_t>());
  } else if (nb::isinstance<nb::str>(h)) {
    return nt::Value::MakeString(h.cast<std::string>());
  } else if (nb::isinstance<nb::bytes>(h)) {
    return nt::Value::MakeRaw(h.cast<std::span<const uint8_t>>());
  } else if (nb::isinstance<nb::none>(h)) {
    throw nb::value_error("Cannot put None into NetworkTable");
  }

  auto seq = h.cast<nb::sequence>();
  if (seq.size() == 0) {
    throw nb::type_error("If you use a list here, cannot be empty");
  }
  // check the first item
  auto i1 = seq[0];
  if (nb::isinstance<nb::bool_>(i1)) {
    auto v = h.cast<std::vector<int>>();
    return nt::Value::MakeBooleanArray(v);
  } else if (nb::isinstance<nb::float_>(i1)) {
    auto v = h.cast<std::vector<double>>();
    return nt::Value::MakeDoubleArray(v);
  } else if (nb::isinstance<nb::int_>(i1)) {
    auto v = h.cast<std::vector<int64_t>>();
    return nt::Value::MakeIntegerArray(v);
  } else if (nb::isinstance<nb::str>(i1)) {
    auto v = h.cast<std::vector<std::string>>();
    return nt::Value::MakeStringArray(v);
  } else {
    throw nb::value_error("Can only put bool/int/float/str/bytes or lists/tuples of them");
  }
}

nb::callable valueFactoryByType(nt::NetworkTableType type) {
  nb::object PyNtValue = nb::module::import("ntcore").attr("Value");
  switch (type) {
  case nt::NetworkTableType::kBoolean:
    return PyNtValue.attr("makeBoolean");
  case nt::NetworkTableType::kDouble:
    return PyNtValue.attr("makeDouble");
  case nt::NetworkTableType::kString:
    return PyNtValue.attr("makeString");
  case nt::NetworkTableType::kRaw:
    return PyNtValue.attr("makeRaw");
  case nt::NetworkTableType::kBooleanArray: 
    return PyNtValue.attr("makeBooleanArray");
  case nt::NetworkTableType::kDoubleArray: 
    return PyNtValue.attr("makeDoubleArray");
  case nt::NetworkTableType::kStringArray:
    return PyNtValue.attr("makeStringArray");
  case nt::NetworkTableType::kInteger:
    return PyNtValue.attr("makeInteger");
  case nt::NetworkTableType::kFloat:
    return PyNtValue.attr("makeFloat");
  case nt::NetworkTableType::kIntegerArray:
    return PyNtValue.attr("makeIntegerArray");
  case nt::NetworkTableType::kFloatArray:
    return PyNtValue.attr("makeFloatArray");
  default:
    throw nb::type_error("empty nt value");
  }
}

}
