

#include <hal/HALBase.h>
#include <hal/Value.h>
#include <rpygen_wrapper.hpp>

RPYBUILD_PYBIND11_MODULE(m) {
  initWrapper(m);

#ifdef __FRC_ROBORIO__
  m.attr("__halplatform__") = "roboRIO";
  m.attr("__hal_simulation__") = false;
#else
  m.attr("__halplatform__") = "sim";
  m.attr("__hal_simulation__") = true;
#endif

  // Add this manually so it can be used from SimValue
  py::enum_<HAL_Type>(m, "Type")
    .value("UNASSIGNED", HAL_Type::HAL_UNASSIGNED)
    .value("BOOLEAN", HAL_Type::HAL_BOOLEAN)
    .value("DOUBLE", HAL_Type::HAL_DOUBLE)
    .value("ENUM", HAL_Type::HAL_ENUM)
    .value("INT", HAL_Type::HAL_INT)
    .value("LONG", HAL_Type::HAL_LONG);


  // Call HAL_Shutdown on module unload
  static int unused; // the capsule needs something to reference
  py::capsule cleanup(&unused, [](void *) { HAL_Shutdown(); });
  m.add_object("_cleanup", cleanup);
}
