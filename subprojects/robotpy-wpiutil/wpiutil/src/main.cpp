
#include <rpygen_wrapper.hpp>

void setup_stack_trace_hook(py::object fn);
void cleanup_stack_trace_hook();

namespace wpi::impl {
void ResetSendableRegistry();
} // namespace wpi::impl

RPYBUILD_PYBIND11_MODULE(m) {
  initWrapper(m);

  static int unused;
  py::capsule cleanup(&unused, [](void *) {
    {
      py::gil_scoped_release unlock;
      wpi::impl::ResetSendableRegistry();
    }

    cleanup_stack_trace_hook();
  });

  m.def("_setup_stack_trace_hook", &setup_stack_trace_hook);
  m.add_object("_st_cleanup", cleanup);
}