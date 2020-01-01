
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

/*
ArrayRef Tests
*/
wpi::ArrayRef<int> load_arrayref_int(wpi::ArrayRef<int> ref) {
    return ref;
}

wpi::ArrayRef<std::string> load_arrayref_string(wpi::ArrayRef<std::string> ref) {
    return ref;
}

wpi::ArrayRef<std::vector<std::string>> load_arrayref_vector(wpi::ArrayRef<std::vector<std::string>> ref) {
    return ref;
}

wpi::ArrayRef<int> cast_arrayref() {
    static std::vector<int> vec{1, 2, 3};
    return vec;
}

RPYBUILD_PYBIND11_MODULE(m) {

    // stringref
    m.def("load_stringref", &load_stringref);
    m.def("cast_stringref", &cast_stringref);
    // ArrayRef
    m.def("load_arrayref_int", &load_arrayref_int);
    m.def("load_arrayref_string", &load_arrayref_string);
    m.def("load_arrayref_vector", &load_arrayref_vector);
};
