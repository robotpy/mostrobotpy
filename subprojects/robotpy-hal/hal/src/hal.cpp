

#include <hal/HALBase.h>
#include <hal/DriverStation.h>
#include <hal/Value.h>
#include <rpygen_wrapper.hpp>

using namespace pybind11::literals;

static py::module_ sys_module;

RPYBUILD_PYBIND11_MODULE(m) {

  // Add this manually so it can be used from SimValue
  py::enum_<HAL_Type>(m, "Type")
    .value("UNASSIGNED", HAL_Type::HAL_UNASSIGNED)
    .value("BOOLEAN", HAL_Type::HAL_BOOLEAN)
    .value("DOUBLE", HAL_Type::HAL_DOUBLE)
    .value("ENUM", HAL_Type::HAL_ENUM)
    .value("INT", HAL_Type::HAL_INT)
    .value("LONG", HAL_Type::HAL_LONG);

  // Add this manually because it would be annoying to do otherwise
  py::class_<HAL_Value>(m, "Value")
    .def_readonly("type", &HAL_Value::type)
    .def_property_readonly("value",
      [](const HAL_Value &self) -> py::object {
        switch (self.type) {
        case HAL_BOOLEAN:
          return py::bool_(self.data.v_boolean);
        case HAL_DOUBLE:
          return py::float_(self.data.v_double);
        case HAL_ENUM:
          return py::int_(self.data.v_enum);
        case HAL_INT:
          return py::int_(self.data.v_int);
        case HAL_LONG:
          return py::int_(self.data.v_long);
        default:
          return py::none();
        }
      }
    )
    .def("__repr__", [](const HAL_Value &self) -> py::str {
      switch (self.type) {
        case HAL_BOOLEAN:
          return "<Value type=bool value=" + std::to_string(self.data.v_boolean) + ">";
        case HAL_DOUBLE:
          return "<Value type=double value=" + std::to_string(self.data.v_double) + ">";
        case HAL_ENUM:
          return "<Value type=enum value=" + std::to_string(self.data.v_enum) + ">";
        case HAL_INT:
          return "<Value type=int value=" + std::to_string(self.data.v_int) + ">";
        case HAL_LONG:
          return "<Value type=long value=" + std::to_string(self.data.v_long) + ">";
        default:
          return "<Value type=invalid>";
        }
    });

  initWrapper(m);

#ifdef __FRC_ROBORIO__
  m.attr("__halplatform__") = "roboRIO";
  m.attr("__hal_simulation__") = false;
#else
  m.attr("__halplatform__") = "sim";
  m.attr("__hal_simulation__") = true;
#endif

  // Redirect stderr to python stderr
  sys_module = py::module_::import("sys");

  HAL_SetPrintErrorImpl([](const char *line, size_t size) {
    py::gil_scoped_acquire lock;
    py::print(py::str(line, size), "file"_a=sys_module.attr("stderr"));
  });

  // Do cleanup on module unload
  static int unused; // the capsule needs something to reference
  py::capsule cleanup(&unused, [](void *) {
    {
      py::gil_scoped_acquire lock;
      HAL_SetPrintErrorImpl(nullptr);
      sys_module.dec_ref();
      sys_module.release();
    }

    {
      py::gil_scoped_release unlock;
      HAL_Shutdown();
    }
  });
  m.add_object("_cleanup", cleanup);
}
