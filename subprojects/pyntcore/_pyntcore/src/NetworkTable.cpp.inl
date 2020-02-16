cls_NetworkTable
    .def("getValue", [](NetworkTable * table, wpi::StringRef key, py::object defaultValue) -> py::object {
        nt::NetworkTableEntry entry;
        {
            py::gil_scoped_release release;
            entry = table->GetEntry(key);
        }
        return pyntcore::GetValueEntry(entry, defaultValue);
    }, py::arg("key"), py::arg("value"))

    // double overload must come before boolean version
    .def("putValue", [](nt::NetworkTable *self, const wpi::Twine &key, double value) {
        return self->PutValue(key, nt::Value::MakeDouble(value));
    }, py::arg("key"), py::arg("value"), release_gil())
    .def("putValue", [](nt::NetworkTable *self, const wpi::Twine &key, bool value) {
        return self->PutValue(key, nt::Value::MakeBoolean(value));
    }, py::arg("key"), py::arg("value"), release_gil())
    .def("putValue", [](nt::NetworkTable *self, const wpi::Twine &key, py::bytes value) {
        return self->PutValue(key, nt::Value::MakeRaw(value.cast<std::string>()));
    }, py::arg("key"), py::arg("value"))
    .def("putValue", [](nt::NetworkTable *self, const wpi::Twine &key, std::string value) {
        return self->PutValue(key, nt::Value::MakeString(value));
    }, py::arg("key"), py::arg("value"), release_gil())
    .def("putValue", [](nt::NetworkTable *self, const wpi::Twine &key, py::sequence value) {
        return self->PutValue(key, pyntcore::py2ntvalue(value));
    }, py::arg("key"), py::arg("value"))

    // double overload must come before boolean version
    .def("setDefaultValue", [](nt::NetworkTable *self, const wpi::Twine &key, double value) {
        return self->SetDefaultValue(key, nt::Value::MakeDouble(value));
    }, py::arg("key"), py::arg("value"), release_gil())
    .def("setDefaultValue", [](nt::NetworkTable *self, const wpi::Twine &key, bool value) {
        return self->SetDefaultValue(key, nt::Value::MakeBoolean(value));
    }, py::arg("key"), py::arg("value"), release_gil())
    .def("setDefaultValue", [](nt::NetworkTable *self, const wpi::Twine &key, py::bytes value) {
        return self->SetDefaultValue(key, nt::Value::MakeRaw(value.cast<std::string>()));
    }, py::arg("key"), py::arg("value"))
    .def("setDefaultValue", [](nt::NetworkTable *self, const wpi::Twine &key, std::string value) {
        return self->SetDefaultValue(key, nt::Value::MakeString(value));
    }, py::arg("key"), py::arg("value"), release_gil())
    .def("setDefaultValue", [](nt::NetworkTable *self, const wpi::Twine &key, py::sequence value) {
        return self->SetDefaultValue(key, pyntcore::py2ntvalue(value));
    }, py::arg("key"), py::arg("value"))

    .def("__contains__", [](nt::NetworkTable *self, const wpi::Twine &key) -> bool {
        return self->ContainsKey(key);
    })
;
