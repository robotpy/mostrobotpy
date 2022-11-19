#include <robotpy_build.h>
#include "nt_instance.h"

namespace pyntcore {

void onInstanceStart(nt::NetworkTableInstance *instance) {
    py::module::import("ntcore._logutil")
        .attr("NtLogForwarder").attr("onInstanceStart")(instance);
}

void onInstancePreReset(nt::NetworkTableInstance *instance) {
    py::module::import("ntcore._logutil")
        .attr("NtLogForwarder").attr("onInstanceDestroy")(instance);
}

void onInstancePostReset(nt::NetworkTableInstance *instance) {
    py::module::import("ntcore.util")
        .attr("_NtProperty").attr("onInstancePostReset")(instance);
}

void onInstanceDestroy(nt::NetworkTableInstance *instance) {
    py::module::import("ntcore._logutil")
        .attr("NtLogForwarder").attr("onInstanceDestroy")(instance);
    py::module::import("ntcore.util")
        .attr("_NtProperty").attr("onInstanceDestroy")(instance);
}


}; // namespace pyntcore