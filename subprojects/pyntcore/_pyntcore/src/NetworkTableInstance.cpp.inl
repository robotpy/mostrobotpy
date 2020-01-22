
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


auto nf = m.def_submodule("NotifyFlags");

nf.attr("IMMEDIATE") = (int)NT_NOTIFY_IMMEDIATE;
nf.attr("LOCAL") = (int)NT_NOTIFY_LOCAL;
nf.attr("NEW") = (int)NT_NOTIFY_NEW;
nf.attr("DELETE") = (int)NT_NOTIFY_DELETE;
nf.attr("UPDATE") = (int)NT_NOTIFY_UPDATE;
nf.attr("FLAGS") = (int)NT_NOTIFY_FLAGS;

cls_NetworkTableInstance.attr("NotifyFlags") = nf;
