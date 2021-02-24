#include "rpygen_wrapper.hpp"

#include <frc2/command/CommandScheduler.h>

#ifndef __FRC_ROBORIO__
#include <hal/Extensions.h>

void commandsOnHalShutdown(void*)
{
    frc2::CommandScheduler::ResetInstance();

    // re-register the callback so that HAL_Shutdown can be called multiple times
    HAL_OnShutdown(NULL, commandsOnHalShutdown);
}

#endif


RPYBUILD_PYBIND11_MODULE(m)
{
    initWrapper(m);

    // ensure that the command data is released when python shuts down
    // even if HAL_Shutdown isn't called
    static int unused; // the capsule needs something to reference
    py::capsule cleanup(&unused, [](void *) {
        frc2::CommandScheduler::ResetInstance();
    });
    m.add_object("_cleanup", cleanup);

#ifndef __FRC_ROBORIO__
    HAL_OnShutdown(nullptr, commandsOnHalShutdown);
#endif
}