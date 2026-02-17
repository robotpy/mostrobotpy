
#include <semiwrap.h>
#include <networktables/NetworkTableEntry.h>
#include <networktables/NetworkTableValue.h>

namespace pyntcore {

nb::object GetBooleanEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue);
nb::object GetDoubleEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue);
nb::object GetFloatEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue);
nb::object GetIntegerEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue);
nb::object GetStringEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue);
nb::object GetRawEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue);
nb::object GetBooleanArrayEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue);
nb::object GetDoubleArrayEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue);
nb::object GetFloatArrayEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue);
nb::object GetIntegerArrayEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue);
nb::object GetStringArrayEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue);
nb::object GetValueEntry(const nt::NetworkTableEntry &entry, nb::object defaultValue);

};
