
#pragma once

#include <ntcore.h>
#include <networktables/NetworkTableInstance.h>

namespace pyntcore {

void attachLogging(nt::NetworkTableInstance *instance);
void detachLogging(nt::NetworkTableInstance *instance);

}; // namespace pyntcore
