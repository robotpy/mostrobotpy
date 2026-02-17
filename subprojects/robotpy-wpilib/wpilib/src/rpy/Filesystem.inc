
// TODO: this should be in a shared library, but robotpy-build does not support that

#include <pybind11/eval.h>
#include <semiwrap.h>

namespace robotnb::filesystem {

static fs::path getMainPath() {
  nb::gil_scoped_acquire gil;
  nb::dict locals;
  nb::exec(R"(
        found = False
        try:
            from robotpy.main import robot_py_path
            if robot_py_path:
                main_path = str(robot_py_path.parent.absolute())
                found = True
        except ImportError:
            pass

        if not found:
            import sys, os.path
            main = sys.modules['__main__'];
            if hasattr(main, '__file__'):
                main_path = os.path.abspath(os.path.dirname(main.__file__))
    )",
           nb::globals(), locals);

  if (locals.contains("main_path")) {
    return fs::path(nb::cast<std::string>(locals["main_path"]));
  } else {
#ifdef __FRC_ROBORIO__
    return fs::path("/home/lvuser/py");
#else
    return fs::current_path();
#endif
  }
}

inline std::string GetOperatingDirectory() {
  return GetOperatingDirectoryFs().string();
}

inline std::string GetDeployDirectory() { return GetDeployDirectoryFs().string(); }

inline fs::path GetOperatingDirectoryFs() {
  static fs::path operatingPath = getMainPath();
  return operatingPath;
}

inline fs::path GetDeployDirectoryFs() { return GetOperatingDirectoryFs() / "deploy"; }

} // namespace robotnb::filesystem