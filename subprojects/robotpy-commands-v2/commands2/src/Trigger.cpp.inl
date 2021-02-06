cls_Trigger
    .def("and_", [](Trigger * self, Trigger * other) {
            return *self && *other;
        }, py::arg("other"),
        "Composes this trigger with another trigger, returning a new trigger that is active when both\n"
        "triggers are active.\n"
        "\n"
        ":param trigger: the trigger to compose with\n"
        "\n"
        ":returns: the trigger that is active when both triggers are active\n")
    .def("or_", [](Trigger * self, Trigger * other) {
            return *self || *other;
        }, py::arg("other"),
        "Composes this trigger with another trigger, returning a new trigger that is active when either\n"
        "triggers are active.\n"
        "\n"
        ":param trigger: the trigger to compose with\n"
        "\n"
        ":returns: the trigger that is active when both triggers are active\n")
    .def("not_", [](Trigger * self) {
            return !*self;
        },
        "Creates a new trigger that is active when this trigger is inactive, i.e. that acts as the\n"
        "negation of this trigger.\n"
        "\n"
        ":param trigger: the trigger to compose with\n"
        "\n"
        ":returns: the trigger that is active when both triggers are active\n");