
#pragma once

#include <wpi/sendable/Sendable.h>
#include <semiwrap.h>

namespace rpy {

//
// These functions must be called with the GIL held
//

void addShuffleboardData(nb::str &key, std::shared_ptr<wpi::Sendable> data);
void clearShuffleboardData();
void destroyShuffleboardData();

} // namespace rpy