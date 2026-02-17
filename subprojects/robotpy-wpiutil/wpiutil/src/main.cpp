
#include <semiwrap_init.wpiutil._wpiutil.hpp>

void setup_stack_trace_hook(nb::object fn);
void cleanup_stack_trace_hook();

void setup_safethread_gil();
void cleanup_safethread_gil();

#ifndef __FRC_ROBORIO__

namespace wpi::impl {
void ResetSendableRegistry();
} // namespace wpi::impl

void cleanup_sendable_registry() {
  // nb::gil_scoped_release unlock; -- TODO: probably released this due to deadlock?
  wpi::impl::ResetSendableRegistry();
}

#else

void cleanup_sendable_registry() {}

#endif

SEMIWRAP_MODULE(m) {
  initWrapper(m);

  static int unused;
  nb::capsule cleanup(&unused, [](void *) noexcept {
    cleanup_sendable_registry();
    cleanup_stack_trace_hook();
    cleanup_safethread_gil();
  });

  setup_safethread_gil();

  m.def("_setup_stack_trace_hook", &setup_stack_trace_hook);
  m.attr("_st_cleanup") = cleanup;
}