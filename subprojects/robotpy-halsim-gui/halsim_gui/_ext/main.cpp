
#include <robotpy_build.h>

#include <HALSimGuiExt.h>
#include <hal/Extensions.h>

RPYBUILD_PYBIND11_MODULE(m) {

  m.def("_kill_on_signal", []() {
    HAL_RegisterExtensionListener(
        nullptr, [](void *, const char *name, void *data) {
          if (std::string_view{name} == HALSIMGUI_EXT_ADDGUILATEEXECUTE) {
            auto AddGuiLateExecute = (halsimgui::AddGuiLateExecuteFn)data;
            AddGuiLateExecute([] {
              py::gil_scoped_acquire gil;
              if (PyErr_CheckSignals() == -1) {
                throw py::error_already_set();
              }
            });
          }
        });
  });
}