
#include "wpystruct.h"

void forEachNested(
    const py::type &t,
    const std::function<void(std::string_view, std::string_view)> &fn) {
  WPyStructInfo info(t);
  wpi::ForEachStructSchema<WPyStruct, WPyStructInfo>(fn, info);
}

py::str getTypeString(const py::type &t) {
  WPyStructInfo info(t);
  return wpi::GetStructTypeString<WPyStruct, WPyStructInfo>(info);
}

py::str getSchema(const py::type &t) {
  WPyStructInfo info(t);
  return wpi::GetStructSchema<WPyStruct, WPyStructInfo>(info);
}

size_t getSize(const py::type &t) {
  WPyStructInfo info(t);
  return wpi::GetStructSize<WPyStruct>(info);
}

py::bytes pack(const WPyStruct &v) {
  WPyStructInfo info(v);

  auto sz = wpi::GetStructSize<WPyStruct>(info);
  PyObject *b = PyBytes_FromStringAndSize(NULL, sz);
  if (b == NULL) {
    throw py::error_already_set();
  }

  char *pybuf;
  py::ssize_t pysz;
  if (PyBytes_AsStringAndSize(b, &pybuf, &pysz) != 0) {
    Py_DECREF(b);
    throw py::error_already_set();
  }

  auto s = std::span((uint8_t *)pybuf, pysz);
  wpi::PackStruct(s, v, info);

  return py::reinterpret_steal<py::bytes>(b);
}

void packInto(const WPyStruct &v, py::buffer &b) {
  WPyStructInfo info(v);
  py::ssize_t sz = wpi::GetStructSize<WPyStruct>(info);

  auto req = b.request();
  if (req.itemsize != 1) {
    throw py::value_error("buffer must only contain bytes");
  } else if (req.ndim != 1) {
    throw py::value_error("buffer must only have a single dimension");
  }

  if (req.size != sz) {
    throw py::value_error("buffer must be " + std::to_string(sz) + " bytes");
  }

  auto s = std::span((uint8_t *)req.ptr, req.size);
  wpi::PackStruct(s, v, info);
}

WPyStruct unpack(const py::type &t, const py::buffer &b) {
  WPyStructInfo info(t);
  py::ssize_t sz = wpi::GetStructSize<WPyStruct>(info);

  auto req = b.request();
  if (req.itemsize != 1) {
    throw py::value_error("buffer must only contain bytes");
  } else if (req.ndim != 1) {
    throw py::value_error("buffer must only have a single dimension");
  }

  if (req.size != sz) {
    throw py::value_error("buffer must be " + std::to_string(sz) + " bytes");
  }

  auto s = std::span((const uint8_t *)req.ptr, req.size);
  return wpi::UnpackStruct<WPyStruct, WPyStructInfo>(s, info);
}

// void unpackInto(const py::buffer &b, WPyStruct *v) {
//   WPyStructInfo info(*v);
//   py::ssize_t sz = wpi::GetStructSize<WPyStruct>(info);

//   auto req = b.request();
//   if (req.itemsize != 1) {
//     throw py::value_error("buffer must only contain bytes");
//   } else if (req.ndim != 1) {
//     throw py::value_error("buffer must only have a single dimension");
//   }

//   if (req.size != sz) {
//     throw py::value_error("buffer must be " + std::to_string(sz) + " bytes");
//   }

//   auto s = std::span((const uint8_t *)req.ptr, req.size);
//   wpi::UnpackStructInto<WPyStruct, WPyStructInfo>(v, s, info);
// }
