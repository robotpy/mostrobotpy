

#include <rpygen_wrapper.hpp>

RPYBUILD_PYBIND11_MODULE(m) {
    initWrapper(m);

#ifdef __FRC_ROBORIO__
    m.attr("__halplatform__") = "roboRIO";
    m.attr("__hal_simulation__") = false;
#else
    m.attr("__halplatform__") = "sim";
    m.attr("__hal_simulation__") = true;
#endif
}
