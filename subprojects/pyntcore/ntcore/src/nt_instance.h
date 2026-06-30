
#pragma once

#include "wpi/nt/NetworkTableInstance.hpp"
#include "wpi/nt/ntcore.h"

namespace pyntcore {

void on_instance_start(wpi::nt::NetworkTableInstance* instance);
void on_instance_pre_reset(wpi::nt::NetworkTableInstance* instance);
void on_instance_post_reset(wpi::nt::NetworkTableInstance* instance);
void on_instance_destroy(wpi::nt::NetworkTableInstance* instance);

void reset_all_instances();

}  // namespace pyntcore
