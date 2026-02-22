
#include <semiwrap_init.ntcore._ntcore.hpp>
#include "nt_instance.h"

SEMIWRAP_MODULE(m) {
  initWrapper(m);

  static int unused;
  nb::capsule cleanup(&unused, [](void *) noexcept {
    pyntcore::resetAllInstances();
  });

  m.attr("_st_cleanup") = cleanup;
}
