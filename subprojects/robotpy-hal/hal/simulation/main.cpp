
#include <rpygen_wrapper.hpp>

void HALSIM_ResetGlobalHandles();
void HALSIM_ResetAllData();

RPYBUILD_PYBIND11_MODULE(m) {
  initWrapper(m);

  m.def(
      "resetGlobalHandles",
      []() {
#ifndef __FRC_ROBORIO__
        HALSIM_ResetGlobalHandles();
#endif
      },
      release_gil());

  m.def(
      "resetAllData",
      []() {
#ifndef __FRC_ROBORIO__
        HALSIM_ResetAllData();
#endif
      },
      release_gil());
}