

#include <hal/HALBase.h>
#include <hal/DriverStation.h>
#include <hal/Value.h>
#include <semiwrap_init.hal._wpiHal.hpp>

using namespace pybind11::literals;

static nb::module_ sys_module;

SEMIWRAP_PYBIND11_MODULE(m) {

  // Add this manually so it can be used from SimValue
  nb::enum_<HAL_Type>(m, "Type")
    .value("UNASSIGNED", HAL_Type::HAL_UNASSIGNED)
    .value("BOOLEAN", HAL_Type::HAL_BOOLEAN)
    .value("DOUBLE", HAL_Type::HAL_DOUBLE)
    .value("ENUM", HAL_Type::HAL_ENUM)
    .value("INT", HAL_Type::HAL_INT)
    .value("LONG", HAL_Type::HAL_LONG);

  // Add this manually because it would be annoying to do otherwise
  nb::class_<HAL_Value>(m, "Value")
    .def_ro("type", &HAL_Value::type)
    .def_prop_ro("value",
      [](const HAL_Value &self) -> nb::object {
        switch (self.type) {
        case HAL_BOOLEAN:
          return nb::bool_(self.data.v_boolean);
        case HAL_DOUBLE:
          return nb::float_(self.data.v_double);
        case HAL_ENUM:
          return nb::int_(self.data.v_enum);
        case HAL_INT:
          return nb::int_(self.data.v_int);
        case HAL_LONG:
          return nb::int_(self.data.v_long);
        default:
          return nb::none();
        }
      }
    )
    .def("__repr__", [](const HAL_Value &self) -> nb::str {
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

  m.def("__test_senderr", []() {
    HAL_SendError(1, 2, 0, "\xfa" "badmessage", "location", "callstack", 1);
  }, release_gil());

#endif

  // Redirect stderr to python stderr
  sys_module = nb::module_::import("sys");

  HAL_SetPrintErrorImpl([](const char *line, size_t size) {
    if (size == 0) {
      return;
    }

    nb::gil_scoped_acquire lock;
    PyObject *o = PyUnicode_DecodeUTF8(line, size, "replace");
    if (o == nullptr) {
      PyErr_Clear();
      nb::print(nb::bytes(line, size), "file"_a=sys_module.attr("stderr"));
    } else {
      nb::print(nb::reinterpret_steal<nb::str>(o), "file"_a=sys_module.attr("stderr"));
    }
  });

  // Do cleanup on module unload
  static int unused; // the capsule needs something to reference
  nb::capsule cleanup(&unused, [](void *) noexcept {
    {
      nb::gil_scoped_acquire lock;
      HAL_SetPrintErrorImpl(nullptr);
      sys_module.dec_ref();
      sys_module.release();
    }

    {
      nb::gil_scoped_release unlock;
      HAL_Shutdown();
    }
  });
  m.add_object("_cleanup", cleanup);
}
