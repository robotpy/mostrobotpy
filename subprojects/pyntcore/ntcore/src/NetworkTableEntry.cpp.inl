cls_NetworkTableEntry
    .def_property_readonly("value", [](const nt::NetworkTableEntry &self) {
        nt::Value v;
        {
            nb::gil_scoped_release release;
            v = self.GetValue();
        }
        return pyntcore::ntvalue2py(v);
    })

    // double overload must come before boolean version
    .def("setValue", [](nt::NetworkTableEntry *self, double value) {
        return self->SetValue(nt::Value::MakeDouble(value));
    }, nb::arg("value"), release_gil())
    .def("setValue", [](nt::NetworkTableEntry *self, bool value) {
        return self->SetValue(nt::Value::MakeBoolean(value));
    }, nb::arg("value"), release_gil())
    .def("setValue", [](nt::NetworkTableEntry *self, nb::bytes value) {
        auto v = nt::Value::MakeRaw(value.cast<std::span<const uint8_t>>());
        nb::gil_scoped_release release;
        return self->SetValue(v);
    }, nb::arg("value"))
    .def("setValue", [](nt::NetworkTableEntry *self, std::string value) {
        return self->SetValue(nt::Value::MakeString(value));
    }, nb::arg("value"), release_gil())
    .def("setValue", [](nt::NetworkTableEntry *self, nb::sequence value) {
        return self->SetValue(pyntcore::py2ntvalue(value));
    }, nb::arg("value"))

    // double overload must come before boolean version
    .def("setDefaultValue", [](nt::NetworkTableEntry *self, double value) {
        return self->SetDefaultValue(nt::Value::MakeDouble(value));
    }, nb::arg("value"), release_gil())
    .def("setDefaultValue", [](nt::NetworkTableEntry *self, bool value) {
        return self->SetDefaultValue(nt::Value::MakeBoolean(value));
    }, nb::arg("value"), release_gil())
    .def("setDefaultValue", [](nt::NetworkTableEntry *self, nb::bytes value) {
        auto v = nt::Value::MakeRaw(value.cast<std::span<const uint8_t>>());
        nb::gil_scoped_release release;
        return self->SetDefaultValue(v);
    }, nb::arg("value"))
    .def("setDefaultValue", [](nt::NetworkTableEntry *self, std::string value) {
        return self->SetDefaultValue(nt::Value::MakeString(value));
    }, nb::arg("value"), release_gil())
    .def("setDefaultValue", [](nt::NetworkTableEntry *self, nb::sequence value) {
        return self->SetDefaultValue(pyntcore::py2ntvalue(value));
    }, nb::arg("value"))
;
