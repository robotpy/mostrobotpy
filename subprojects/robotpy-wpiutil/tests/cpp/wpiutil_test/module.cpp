
#include <robotpy_build.h>

#include <wpiutil_converters.hpp>


std::string load_stringref(wpi::StringRef ref) {
    return ref.str();
}

wpi::StringRef cast_stringref() {
    // StringRef refers to a thing -- static ensures the ref is valid
    static std::string casted("casted");
    return casted;
}


RPYBUILD_PYBIND11_MODULE(m) {

    // stringref
    m.def("load_stringref", &load_stringref);
    m.def("cast_stringref", &cast_stringref);
}