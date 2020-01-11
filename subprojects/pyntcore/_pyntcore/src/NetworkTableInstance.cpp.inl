
cls_NetworkTableInstance
    .def("initialize", [](NetworkTableInstance * that, const std::string& server) {
            if (server.length() > 0) {
                that->StartClient(server.c_str());
            } else {
                that->StartServer();
            }
        }, 
        py::arg("server")="", 
        release_gil())
    .def("getGlobalTable", [](NetworkTableInstance * that) {
        return that->GetTable("/");
    }, release_gil())
    .def("getGlobalAutoUpdateValue", [](NetworkTableInstance * that,
        const wpi::Twine &key, py::handle defaultValue, bool writeDefault) {
        auto dv = pyntcore::py2ntvalue(defaultValue);

        py::gil_scoped_release release;
        auto entry = that->GetEntry(key);
        if (writeDefault) {
            entry.ForceSetValue(dv);
        } else {
            entry.SetDefaultValue(dv);
        }
        return entry;
    });