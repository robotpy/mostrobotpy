#pragma once

#include <semiwrap.h>

#include "wpi/nt/NetworkTableEntry.hpp"
#include "wpi/nt/NetworkTableValue.hpp"

namespace pyntcore {

py::object GetBooleanEntry(const wpi::nt::NetworkTableEntry& entry,
                           py::object default_value);
py::object GetDoubleEntry(const wpi::nt::NetworkTableEntry& entry,
                          py::object default_value);
py::object GetFloatEntry(const wpi::nt::NetworkTableEntry& entry,
                         py::object default_value);
py::object GetIntegerEntry(const wpi::nt::NetworkTableEntry& entry,
                           py::object default_value);
py::object GetStringEntry(const wpi::nt::NetworkTableEntry& entry,
                          py::object default_value);
py::object GetRawEntry(const wpi::nt::NetworkTableEntry& entry,
                       py::object default_value);
py::object GetBooleanArrayEntry(const wpi::nt::NetworkTableEntry& entry,
                                py::object default_value);
py::object GetDoubleArrayEntry(const wpi::nt::NetworkTableEntry& entry,
                               py::object default_value);
py::object GetFloatArrayEntry(const wpi::nt::NetworkTableEntry& entry,
                              py::object default_value);
py::object GetIntegerArrayEntry(const wpi::nt::NetworkTableEntry& entry,
                                py::object default_value);
py::object GetStringArrayEntry(const wpi::nt::NetworkTableEntry& entry,
                               py::object default_value);
py::object GetValueEntry(const wpi::nt::NetworkTableEntry& entry,
                         py::object default_value);

}  // namespace pyntcore
