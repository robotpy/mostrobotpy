
#include <rpygen_wrapper.hpp>
#include "nt_instance.h"

RPYBUILD_PYBIND11_MODULE(m) {
  initWrapper(m);

  static int unused;
  py::capsule cleanup(&unused, [](void *) {
    pyntcore::resetAllInstances();
  });

  m.add_object("_st_cleanup", cleanup);
}