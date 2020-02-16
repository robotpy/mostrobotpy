cls_NetworkTableEntry
    .def_property_readonly("value", [](nt::NetworkTableEntry * that) {
        auto v = that->GetValue();
        return pyntcore::ntvalue2py(v.get());
    })

    // double overload must come before boolean version
    .def("setValue", [](nt::NetworkTableEntry *self, double value) {
        return self->SetValue(nt::Value::MakeDouble(value));
    }, py::arg("value"), release_gil())
    .def("setValue", [](nt::NetworkTableEntry *self, bool value) {
        return self->SetValue(nt::Value::MakeBoolean(value));
    }, py::arg("value"), release_gil())
    .def("setValue", [](nt::NetworkTableEntry *self, py::bytes value) {
        return self->SetValue(nt::Value::MakeRaw(value.cast<std::string>()));
    }, py::arg("value"))
    .def("setValue", [](nt::NetworkTableEntry *self, std::string value) {
        return self->SetValue(nt::Value::MakeString(value));
    }, py::arg("value"), release_gil())
    .def("setValue", [](nt::NetworkTableEntry *self, py::sequence value) {
        return self->SetValue(pyntcore::py2ntvalue(value));
    }, py::arg("value"))

    // double overload must come before boolean version
    .def("setDefaultValue", [](nt::NetworkTableEntry *self, double value) {
        return self->SetDefaultValue(nt::Value::MakeDouble(value));
    }, py::arg("value"), release_gil())
    .def("setDefaultValue", [](nt::NetworkTableEntry *self, bool value) {
        return self->SetDefaultValue(nt::Value::MakeBoolean(value));
    }, py::arg("value"), release_gil())
    .def("setDefaultValue", [](nt::NetworkTableEntry *self, py::bytes value) {
        return self->SetDefaultValue(nt::Value::MakeRaw(value.cast<std::string>()));
    }, py::arg("value"))
    .def("setDefaultValue", [](nt::NetworkTableEntry *self, std::string value) {
        return self->SetDefaultValue(nt::Value::MakeString(value));
    }, py::arg("value"), release_gil())
    .def("setDefaultValue", [](nt::NetworkTableEntry *self, py::sequence value) {
        return self->SetDefaultValue(pyntcore::py2ntvalue(value));
    }, py::arg("value"))

    // double overload must come before boolean version
    .def("forceSetValue", [](nt::NetworkTableEntry *self, double value) {
        self->ForceSetValue(nt::Value::MakeDouble(value));
    }, py::arg("value"), release_gil())
    .def("forceSetValue", [](nt::NetworkTableEntry *self, bool value) {
        self->ForceSetValue(nt::Value::MakeBoolean(value));
    }, py::arg("value"), release_gil())
    .def("forceSetValue", [](nt::NetworkTableEntry *self, py::bytes value) {
        self->ForceSetValue(nt::Value::MakeRaw(value.cast<std::string>()));
    }, py::arg("value"))
    .def("forceSetValue", [](nt::NetworkTableEntry *self, std::string value) {
        self->ForceSetValue(nt::Value::MakeString(value));
    }, py::arg("value"), release_gil())
    .def("forceSetValue", [](nt::NetworkTableEntry *self, py::sequence value) {
        self->ForceSetValue(pyntcore::py2ntvalue(value));
    }, py::arg("value"))
;
