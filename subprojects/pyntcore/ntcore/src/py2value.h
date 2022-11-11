
#include <robotpy_build.h>
#include <networktables/NetworkTableValue.h>
#include <networktables/NetworkTableType.h>

namespace pyntcore {

const char * nttype2str(NT_Type type);

py::object ntvalue2py(const nt::Value &ntvalue);

nt::Value py2ntvalue(py::handle h);

py::cpp_function valueFactoryByType(nt::NetworkTableType type);

};