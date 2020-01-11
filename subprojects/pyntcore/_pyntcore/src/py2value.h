
#include <robotpy_build.h>
#include <networktables/NetworkTableValue.h>
#include <networktables/NetworkTableType.h>

namespace pyntcore {

py::object ntvalue2py(nt::Value * ntvalue);

std::shared_ptr<nt::NetworkTableValue> py2ntvalue(py::handle h);

py::cpp_function valueFactoryByType(nt::NetworkTableType type);

};