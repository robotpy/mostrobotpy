
#include "py2value.h"

#include <vector>

// type casters
#include <pybind11/stl.h>
#include <wpi_arrayref_type_caster.h>
#include <wpi_twine_type_caster.h>




namespace pyntcore {


py::object ntvalue2py(nt::Value * ntvalue) {
  auto v = ntvalue->value();
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
    return std::move(py::cast(ntvalue->GetStringArray()));
  }

  default:
    return py::none();
  }
}

std::shared_ptr<nt::NetworkTableValue> py2ntvalue(py::handle h) {
  if (py::isinstance<py::bool_>(h)) {
    return nt::NetworkTableValue::MakeBoolean(h.cast<bool>());
  } else if (py::isinstance<py::float_>(h) || py::isinstance<py::int_>(h)) {
    return nt::NetworkTableValue::MakeDouble(h.cast<double>());
  } else if (py::isinstance<py::str>(h)) {
    return nt::NetworkTableValue::MakeString(h.cast<std::string>());
  } else if (py::isinstance<py::bytes>(h)) {
    return nt::NetworkTableValue::MakeRaw(h.cast<std::string>());
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
    return nt::NetworkTableValue::MakeBooleanArray(v);
  } else if (py::isinstance<py::float_>(i1) || py::isinstance<py::int_>(i1)) {
    auto v = h.cast<std::vector<double>>();
    return nt::NetworkTableValue::MakeDoubleArray(v);
  } else if (py::isinstance<py::str>(i1)) {
    auto v = h.cast<std::vector<std::string>>();
    return nt::NetworkTableValue::MakeStringArray(v);
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
    return py::cpp_function([](const wpi::Twine &v) { return nt::Value::MakeString(v); });
  case nt::NetworkTableType::kRaw:
    return py::cpp_function([](const wpi::Twine &v) { return nt::Value::MakeString(v); });
  case nt::NetworkTableType::kBooleanArray: 
    return py::cpp_function([](const wpi::ArrayRef<bool> &v) { return nt::Value::MakeBooleanArray(v); });
  case nt::NetworkTableType::kDoubleArray: 
    return py::cpp_function([](const wpi::ArrayRef<double> &v) { return nt::Value::MakeDoubleArray(v); });
  case nt::NetworkTableType::kStringArray:
    return py::cpp_function([](const wpi::ArrayRef<std::string> &v) { return nt::Value::MakeStringArray(v); });
  default:
    throw py::type_error("empty nt value");
  }
}

}
