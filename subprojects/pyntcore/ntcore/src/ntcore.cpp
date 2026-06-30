
#include "nt_instance.h"
#include "semiwrap_init.ntcore._ntcore.hpp"

SEMIWRAP_PYBIND11_MODULE(m) {
  initWrapper(m);

  static int unused;
  py::capsule cleanup(&unused, [](void*) { pyntcore::reset_all_instances(); });

  m.add_object("_st_cleanup", cleanup);
}
