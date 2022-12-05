
#include <rpygen_wrapper.hpp>

#include "cscore_cpp.h"

RPYBUILD_PYBIND11_MODULE(m) {
    initWrapper(m);

    static int unused; // the capsule needs something to reference
    py::capsule cleanup(&unused, [](void *) {
        // don't release gil until after calling this
        cs::SetDefaultLogger(20 /* WPI_LOG_INFO */);
        
        // but this MUST release the gil, or deadlock may occur
        py::gil_scoped_release __release;
        CS_Shutdown();
    });
    m.add_object("_cleanup", cleanup);
}