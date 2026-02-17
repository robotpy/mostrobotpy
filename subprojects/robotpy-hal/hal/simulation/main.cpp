
#include <semiwrap_init.hal.simulation._simulation.hpp>
#include <nanobind/stl/function.h>

#include "sim_cb.h"
#include "sim_value_cb.h"

void HALSIM_ResetGlobalHandles();

SEMIWRAP_PYBIND11_MODULE(m) {

  nb::class_<SimCB> cls_SimCB(m, "SimCB");
  cls_SimCB.doc() = "Simulation callback handle";
  cls_SimCB.def("cancel", &SimCB::Cancel, nb::doc("Cancel the callback"));

  nb::class_<SimValueCB> cls_SimValueCB(m, "SimValueCB");
  cls_SimValueCB.doc() = "Simulation callback handle";
  cls_SimValueCB.def("cancel", &SimValueCB::Cancel, nb::doc("Cancel the callback"));

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