
#include <robotpy_build.h>
#include <networktables/NetworkTableEntry.h>
#include <networktables/NetworkTableValue.h>

namespace pyntcore {

py::object GetBooleanEntry(nt::NetworkTableEntry &entry, py::object &defaultValue);
py::object GetDoubleEntry(nt::NetworkTableEntry &entry, py::object &defaultValue);
py::object GetStringEntry(nt::NetworkTableEntry &entry, py::object &defaultValue);
py::object GetRawEntry(nt::NetworkTableEntry &entry, py::object &defaultValue);
py::object GetBooleanArrayEntry(nt::NetworkTableEntry &entry, py::object &defaultValue);
py::object GetDoubleArrayEntry(nt::NetworkTableEntry &entry, py::object &defaultValue);
py::object GetStringArrayEntry(nt::NetworkTableEntry &entry, py::object &defaultValue);
py::object GetValueEntry(nt::NetworkTableEntry &entry, py::object &defaultValue);

};