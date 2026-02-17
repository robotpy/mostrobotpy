cls_NetworkTable
    .def("getValue", [](const NetworkTable &self, std::string_view key, nb::object defaultValue) -> nb::object {
        nt::NetworkTableEntry entry;
        {
            nb::gil_scoped_release release;
            entry = self.GetEntry(key);
        }
        return pyntcore::GetValueEntry(entry, defaultValue);
    }, nb::arg("key"), nb::arg("value"))

    // double overload must come before boolean version
    .def("putValue", [](nt::NetworkTable *self, std::string_view key, double value) {
        return self->PutValue(key, nt::Value::MakeDouble(value));
    }, nb::arg("key"), nb::arg("value"), release_gil())
    .def("putValue", [](nt::NetworkTable *self, std::string_view key, bool value) {
        return self->PutValue(key, nt::Value::MakeBoolean(value));
    }, nb::arg("key"), nb::arg("value"), release_gil())
    .def("putValue", [](nt::NetworkTable *self, std::string_view key, nb::bytes value) {
        auto v = nt::Value::MakeRaw(value.cast<std::span<const uint8_t>>());
        nb::gil_scoped_release release;
        return self->PutValue(key, v);
    }, nb::arg("key"), nb::arg("value"))
    .def("putValue", [](nt::NetworkTable *self, std::string_view key, std::string value) {
        return self->PutValue(key, nt::Value::MakeString(std::move(value)));
    }, nb::arg("key"), nb::arg("value"), release_gil())
    .def("putValue", [](nt::NetworkTable *self, std::string_view key, nb::sequence value) {
        auto v = pyntcore::py2ntvalue(value);
        nb::gil_scoped_release release;
        return self->PutValue(key, v);
    }, nb::arg("key"), nb::arg("value"))

    // double overload must come before boolean version
    .def("setDefaultValue", [](nt::NetworkTable *self, std::string_view key, double value) {
        return self->SetDefaultValue(key, nt::Value::MakeDouble(value));
    }, nb::arg("key"), nb::arg("value"), release_gil())
    .def("setDefaultValue", [](nt::NetworkTable *self, std::string_view key, bool value) {
        return self->SetDefaultValue(key, nt::Value::MakeBoolean(value));
    }, nb::arg("key"), nb::arg("value"), release_gil())
    .def("setDefaultValue", [](nt::NetworkTable *self, std::string_view key, nb::bytes value) {
        auto v = nt::Value::MakeRaw(value.cast<std::span<const uint8_t>>());
        nb::gil_scoped_release release;
        return self->SetDefaultValue(key, v);
    }, nb::arg("key"), nb::arg("value"))
    .def("setDefaultValue", [](nt::NetworkTable *self, std::string_view key, std::string value) {
        return self->SetDefaultValue(key, nt::Value::MakeString(std::move(value)));
    }, nb::arg("key"), nb::arg("value"), release_gil())
    .def("setDefaultValue", [](nt::NetworkTable *self, std::string_view key, nb::sequence value) {
        auto v = pyntcore::py2ntvalue(value);
        nb::gil_scoped_release release;
        return self->SetDefaultValue(key, v);
    }, nb::arg("key"), nb::arg("value"))

    .def("__contains__", [](const nt::NetworkTable &self, std::string_view key) -> bool {
        return self.ContainsKey(key);
    }, release_gil())
;
