
cls_Value
  .def_static("makeValue", [](py::handle value) {
      return pyntcore::py2ntvalue(value);
    }, py::arg("value"))
  .def_static("getFactoryByType", [](nt::NetworkTableType type) {
    return pyntcore::valueFactoryByType(type);
  });