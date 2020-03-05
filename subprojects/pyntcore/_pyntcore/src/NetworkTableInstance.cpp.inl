
cls_NetworkTableInstance
    .def("initialize", [](NetworkTableInstance * that, const std::string& server) {
            pyntcore::attachLogging(that->GetHandle());
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
    })
    .def("addEntryListener", [](NetworkTableInstance * that,
        std::function<void(std::string, py::object, int)> listener,
        bool immediateNotify, bool localNotify, bool paramIsNew) {

        unsigned int flags = NT_NOTIFY_NEW | NT_NOTIFY_UPDATE;
        if (immediateNotify) {
            flags |= NT_NOTIFY_IMMEDIATE;
        }
        if (localNotify) {
            flags |= NT_NOTIFY_LOCAL;
        }

        // TODO: replace this with a polling thread

        return that->AddEntryListener("/",
            [listener, paramIsNew](const EntryNotification &event) {
                py::gil_scoped_acquire acquire;
                if (paramIsNew) {
                    listener(event.name, pyntcore::ntvalue2py(event.value.get()),
                             event.flags | NT_NOTIFY_NEW ? 1 : 0);
                } else {
                    listener(event.name, pyntcore::ntvalue2py(event.value.get()),
                             event.flags);
                }
            },
            flags);
    },
        py::arg("listener"),
        py::arg("immediateNotify")=true,
        py::arg("localNotify")=true,
        py::arg("paramIsNew")=true,
        release_gil()
    )
    .def("isServer", [](NetworkTableInstance * self) -> bool {
        return self->GetNetworkMode() & NT_NET_MODE_SERVER;
    })
    .def("getRemoteAddress", [](NetworkTableInstance * self) -> py::object {
        if (!(self->GetNetworkMode() & NT_NET_MODE_SERVER)) {
            for (auto conn: self->GetConnections()) {
                return py::str(conn.remote_ip);
            }
        }
        return py::none();
    });


auto nf = m.def_submodule("NotifyFlags");

nf.attr("IMMEDIATE") = (int)NT_NOTIFY_IMMEDIATE;
nf.attr("LOCAL") = (int)NT_NOTIFY_LOCAL;
nf.attr("NEW") = (int)NT_NOTIFY_NEW;
nf.attr("DELETE") = (int)NT_NOTIFY_DELETE;
nf.attr("UPDATE") = (int)NT_NOTIFY_UPDATE;
nf.attr("FLAGS") = (int)NT_NOTIFY_FLAGS;

cls_NetworkTableInstance.attr("NotifyFlags") = nf;
