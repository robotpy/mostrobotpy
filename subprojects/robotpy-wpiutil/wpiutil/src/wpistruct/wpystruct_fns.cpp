
#include <nanobind/ndarray.h>
#include <nanobind/stl/string_view.h>

#include "wpystruct.h"

void forEachNested(
    const nb::type_object &t,
    const std::function<void(std::string_view, std::string_view)> &fn) {
  WPyStructInfo info(t);
  wpi::ForEachStructSchema<WPyStruct, WPyStructInfo>(fn, info);
}

nb::str getTypeName(const nb::type_object &t) {
  WPyStructInfo info(t);
  return nb::borrow<nb::str>(nb::cast(wpi::GetStructTypeName<WPyStruct, WPyStructInfo>(info)));
}

nb::str getSchema(const nb::type_object &t) {
  WPyStructInfo info(t);
  return nb::borrow<nb::str>(nb::cast(wpi::GetStructSchema<WPyStruct, WPyStructInfo>(info)));
}

size_t getSize(const nb::type_object &t) {
  WPyStructInfo info(t);
  return wpi::GetStructSize<WPyStruct>(info);
}

nb::bytes pack(const WPyStruct &v) {
  WPyStructInfo info(v);

  auto sz = wpi::GetStructSize<WPyStruct>(info);
  PyObject *b = PyBytes_FromStringAndSize(NULL, sz);
  if (b == NULL) {
    throw nb::python_error();
  }

  char *pybuf;
  nb::ssize_t pysz;
  if (PyBytes_AsStringAndSize(b, &pybuf, &pysz) != 0) {
    Py_DECREF(b);
    throw nb::python_error();
  }

  auto s = std::span((uint8_t *)pybuf, pysz);
  wpi::PackStruct(s, v, info);

  return nb::steal<nb::bytes>(b);
}

nb::bytes packArray(const nb::sequence &seq) {
  auto len = PySequence_Length(seq.ptr());
  if (len < 0) {
    throw nb::python_error();
  }

  if (len == 0) {
    return {};
  }

  WPyStructInfo info(nb::borrow<nb::type_object>(seq[0].type()));
  auto sz = wpi::GetStructSize<WPyStruct>(info);
  auto total = sz*len;

  PyObject *b = PyBytes_FromStringAndSize(NULL, total);
  if (b == NULL) {
    throw nb::python_error();
  }

  char *pybuf;
  nb::ssize_t pysz;
  if (PyBytes_AsStringAndSize(b, &pybuf, &pysz) != 0) {
    Py_DECREF(b);
    throw nb::python_error();
  }

  nb::bytes bytes_obj(nb::steal(b));

  for (const auto &v: seq) {
    WPyStruct wv(nb::borrow(v));
    auto s = std::span((uint8_t *)pybuf, sz);
    wpi::PackStruct(s, wv, info);
    pybuf += sz;
  }

  return bytes_obj;
}

void packInto(const WPyStruct &v, const nb::ndarray<uint8_t, nb::shape<-1>, nb::c_contig> &buf) {
  WPyStructInfo info(v);
  auto sz = wpi::GetStructSize<WPyStruct>(info);

  if (buf.size() != sz) {
    std::string msg = "buffer must be " + std::to_string(sz) + " bytes";
    throw nb::value_error(msg.c_str());
  }

  auto s = std::span(buf.data(), buf.size());
  wpi::PackStruct(s, v, info);
}

WPyStruct unpack(const nb::type_object &t, const nb::ndarray<const uint8_t, nb::shape<-1>, nb::c_contig> &buf) {
  WPyStructInfo info(t);
  auto sz = wpi::GetStructSize<WPyStruct>(info);

  if (buf.size() != sz) {
    std::string msg = "buffer must be " + std::to_string(sz) + " bytes";
    throw nb::value_error(msg.c_str());
  }

  auto s = std::span(buf.data(), buf.size());
  return wpi::UnpackStruct<WPyStruct, WPyStructInfo>(s, info);
}

nb::typed<nb::list, WPyStruct> unpackArray(const nb::type_object &t, const nb::ndarray<const uint8_t, nb::shape<-1>, nb::c_contig> &buf) {
  WPyStructInfo info(t);
  auto sz = wpi::GetStructSize<WPyStruct>(info);

  if (buf.size() % sz != 0) {
    std::string msg = "buffer must be multiple of " + std::to_string(sz) + " bytes";
    throw nb::value_error(msg.c_str());
  }

  auto items = buf.size() / sz;
  nb::object a(nb::steal(PyList_New(items)));
  if (!a.is_valid()) {
    throw nb::python_error();
  }

  const uint8_t *ptr = buf.data();
  for (size_t i = 0; i < items; i++) {
    auto s = std::span(ptr, sz);
    auto v = wpi::UnpackStruct<WPyStruct, WPyStructInfo>(s, info);
    // steals a reference
    NB_LIST_SET_ITEM(a.ptr(), i, v.py.inc_ref().ptr());
    ptr += sz;
  }

  return nb::list(a);
}

// void unpackInto(const nb::buffer &b, WPyStruct *v) {
//   WPyStructInfo info(*v);
//   auto sz = wpi::GetStructSize<WPyStruct>(info);

//   auto req = b.request();
//   if (req.itemsize != 1) {
//     throw nb::value_error("buffer must only contain bytes");
//   } else if (req.ndim != 1) {
//     throw nb::value_error("buffer must only have a single dimension");
//   }

//   if (req.size != sz) {
//     throw nb::value_error("buffer must be " + std::to_string(sz) + " bytes");
//   }

//   auto s = std::span((const uint8_t *)req.ptr, req.size);
//   wpi::UnpackStructInto<WPyStruct, WPyStructInfo>(v, s, info);
// }
