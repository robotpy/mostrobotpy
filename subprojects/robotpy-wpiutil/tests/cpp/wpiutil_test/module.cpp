// clang-format off
#include <robotpy_build.h>

#include <wpi_array_type_caster.h>
#include <wpi_span_type_caster.h>
#include <wpi_smallset_type_caster.h>
#include <wpi_smallvector_type_caster.h>
#include <wpi_smallvectorimpl_type_caster.h>

/*
array tests
*/
wpi::array<int, 4> load_array_int(wpi::array<int, 4> data) {
    return data;
}

wpi::array<int, 1> load_array_int1(wpi::array<int, 1> data) {
    return data;
}

/*
span Tests
*/
wpi::span<const int> load_span_int(wpi::span<const int> ref) {
    return ref;
}

wpi::span<const bool> load_span_bool(wpi::span<const bool> ref) {
    return ref;
}

wpi::span<std::string> load_span_string(wpi::span<std::string> ref) {
    return ref;
}

wpi::span<const std::string> load_span_string_const(wpi::span<const std::string> ref) {
    return ref;
}

wpi::span<std::string_view> load_span_string_view(wpi::span<std::string_view> ref) {
    return ref;
}

wpi::span<std::vector<std::string>> load_span_vector(wpi::span<std::vector<std::string>> ref) {
    return ref;
}

wpi::span<int> cast_span() {
    static std::vector<int> vec{1, 2, 3};
    return vec;
}

wpi::span<const std::string> make_string_span() {
    static std::vector<std::string> vec{"hi", "there"};
    return vec;
}

py::object cast_string_span() {
    return py::cast(make_string_span());
}

wpi::span<const uint8_t> load_span_bytes(wpi::span<const uint8_t> ref) {
    return ref;
}

void modify_span_buffer(wpi::span<uint8_t> ref) {
    ref[0] = 0x4;
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

    // array
    m.def("load_array_int", &load_array_int);
    m.def("load_array_int1", &load_array_int1);
    // span
    m.def("load_span_int", &load_span_int);
    m.def("load_span_bool", &load_span_bool);
    m.def("load_span_string", &load_span_string);
    m.def("load_span_string_const", &load_span_string_const);
    m.def("load_span_string_view", &load_span_string_view);
    m.def("load_span_vector", &load_span_vector);
    m.def("cast_span", &cast_span);
    m.def("cast_string_span", &cast_string_span);
    m.def("load_span_bytes", &load_span_bytes);
    m.def("modify_span_buffer", &modify_span_buffer);
    // SmallSet
    m.def("load_smallset_int", &load_smallset_int);
    m.def("cast_smallset", &cast_smallset);
    // SmallVector
    m.def("load_smallvec_int", &load_smallvec_int);
    m.def("cast_smallvec", &cast_smallvec);
    // SmallVectorImpl
    m.def("load_smallvecimpl_int", &load_smallvecimpl_int);
};
