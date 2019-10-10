
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

// forward declarations
void init_NetworkTable(py::module &m);
void init_NetworkTableEntry(py::module &m);
void init_NetworkTableInstance(py::module &m);
void init_NetworkTableType(py::module &m);

PYBIND11_MODULE(ntcore, m)
{
  init_NetworkTable(m);
  init_NetworkTableEntry(m);
  init_NetworkTableInstance(m);
  init_NetworkTableType(m);
}
