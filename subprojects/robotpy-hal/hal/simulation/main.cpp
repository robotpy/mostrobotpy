
#include <rpygen_wrapper.hpp>
#include <pybind11/functional.h>

#include "sim_cb.h"

void HALSIM_ResetGlobalHandles();

RPYBUILD_PYBIND11_MODULE(m) {

  py::class_<SimCB> cls_SimCB(m, "SimCB");
  cls_SimCB.doc() = "Simulation callback handle";
  cls_SimCB.def("cancel", &SimCB::Cancel, py::doc("Cancel the callback"));

  initWrapper(m);

  m.def(
      "resetGlobalHandles",
      []() {
#ifndef __FRC_ROBORIO__
        HALSIM_ResetGlobalHandles();
#endif
      },
      release_gil());
}