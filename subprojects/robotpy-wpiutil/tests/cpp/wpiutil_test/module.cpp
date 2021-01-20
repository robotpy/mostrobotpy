// clang-format off
#include <robotpy_build.h>

#include <wpi_array_type_caster.h>
#include <wpi_arrayref_type_caster.h>
#include <wpi_smallset_type_caster.h>
#include <wpi_smallvector_type_caster.h>
#include <wpi_smallvectorimpl_type_caster.h>
#include <wpi_stringref_type_caster.h>
#include <wpi_twine_type_caster.h>

std::string load_stringref(wpi::StringRef ref) {
    return ref.str();
}

wpi::StringRef cast_stringref() {
    // StringRef refers to a thing -- static ensures the ref is valid
    static std::string casted("casted");
    return casted;
}

/*
array tests
*/
wpi::array<int, 4> load_array_int(wpi::array<int, 4> data) {
    return data;
}

/*
ArrayRef Tests
*/
wpi::ArrayRef<int> load_arrayref_int(wpi::ArrayRef<int> ref) {
    return ref;
}

wpi::ArrayRef<bool> load_arrayref_bool(wpi::ArrayRef<bool> ref) {
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

/*
SmallSet tests
*/

wpi::SmallSet<int, 4> load_smallset_int(wpi::SmallSet<int, 4> ref) {
    return ref;
}

wpi::SmallSet<int, 4> cast_smallset() {
    static wpi::SmallSet<int, 4> set;
    set.insert(1);
    set.insert(2);
    set.insert(3);
    set.insert(4);
    return set;
}

/*
SmallVector tests
*/

wpi::SmallVector<int, 4> load_smallvec_int(wpi::SmallVector<int, 4> ref) {
    return ref;
}

wpi::SmallVector<int, 4> cast_smallvec() {
    static wpi::SmallVector<int, 4> set;
    set.append({1, 2, 3, 4});
    return set;
}

/*
SmallVectorImpl tests

.. seems like references are the only useful things to do with them
*/

wpi::SmallVectorImpl<int>&  load_smallvecimpl_int(wpi::SmallVectorImpl<int>& ref) {
    static wpi::SmallVector<int, 4> set(ref.begin(), ref.end());
    return set;
}

RPYBUILD_PYBIND11_MODULE(m) {

    // stringref
    m.def("load_stringref", &load_stringref);
    m.def("cast_stringref", &cast_stringref);
    // array
    m.def("load_array_int", &load_array_int);
    // ArrayRef
    m.def("load_arrayref_int", &load_arrayref_int);
    m.def("load_arrayref_bool", &load_arrayref_bool);
    m.def("load_arrayref_string", &load_arrayref_string);
    m.def("load_arrayref_vector", &load_arrayref_vector);
    // SmallSet
    m.def("load_smallset_int", &load_smallset_int);
    m.def("cast_smallset", &cast_smallset);
    // SmallVector
    m.def("load_smallvec_int", &load_smallvec_int);
    m.def("cast_smallvec", &cast_smallvec);
    // SmallVectorImpl
    m.def("load_smallvecimpl_int", &load_smallvecimpl_int);
};
