cls_NetworkTable
    .def("putValue", [](nt::NetworkTable *self, const wpi::Twine &key, bool value) {
        return self->PutValue(key, nt::Value::MakeBoolean(value));
    }, py::arg("key"), py::arg("value"), release_gil())
    .def("putValue", [](nt::NetworkTable *self, const wpi::Twine &key, double value) {
        return self->PutValue(key, nt::Value::MakeDouble(value));
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
;
