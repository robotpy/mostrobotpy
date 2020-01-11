cls_NetworkTableEntry
    .def_property_readonly("value", [](nt::NetworkTableEntry * that) {
        auto v = that->GetValue();
        return pyntcore::ntvalue2py(v.get());
    });