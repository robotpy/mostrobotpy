
#include <semiwrap_init.halsim_gui._ext._halsim_gui_ext.hpp>

#include <HALSimGuiExt.h>
#include <hal/Extensions.h>

SEMIWRAP_PYBIND11_MODULE(m) {

  initWrapper(m);

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