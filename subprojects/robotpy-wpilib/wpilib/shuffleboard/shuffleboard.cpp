
#include "semiwrap_init.wpilib.shuffleboard._shuffleboard.hpp"
#include "ShuffleboardData.h"

SEMIWRAP_PYBIND11_MODULE(m)
{
    initWrapper(m);

    // ensure that the shuffleboard data is released when python shuts down
    static int unused; // the capsule needs something to reference
    nb::capsule cleanup(&unused, [](void *) noexcept {
        rnb::destroyShuffleboardData();
    });
    m.attr("_sbd_cleanup") = cleanup;
    m.def("_clearShuffleboardData", &rnb::clearShuffleboardData);
}
