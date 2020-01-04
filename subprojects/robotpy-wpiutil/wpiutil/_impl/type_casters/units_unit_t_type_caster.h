#pragma once

#include <pybind11/pybind11.h>
#include <units/units.h>

namespace pybind11
{
namespace detail
{

#define PYBIND_UNIT_NAME(unit_name, plural)                \
template <> struct handle_type_name<units::unit_name##_t>  \
{ static constexpr auto name = _(#plural); }

PYBIND_UNIT_NAME(second, seconds);
PYBIND_UNIT_NAME(millisecond, milliseconds);
PYBIND_UNIT_NAME(nanosecond, nanoseconds);
PYBIND_UNIT_NAME(meter, meters);
PYBIND_UNIT_NAME(foot, feet);
PYBIND_UNIT_NAME(meters_per_second, meters_per_second);
PYBIND_UNIT_NAME(feet_per_second, feet_per_second);
PYBIND_UNIT_NAME(degree, degrees);
PYBIND_UNIT_NAME(radian, radians);
PYBIND_UNIT_NAME(radians_per_second, radians_per_second);
PYBIND_UNIT_NAME(volt, volts);
PYBIND_UNIT_NAME(turn, turns);

#undef PYBIND_UNIT_NAME


template<class U, typename T, template<typename> class S>
struct type_caster<units::unit_t<U, T, S>> {
    using value_type = units::unit_t<U, T, S>;

    // TODO: there should be a way to include the type with this
    PYBIND11_TYPE_CASTER(value_type, handle_type_name<value_type>::name);

    bool load(handle src, bool convert) {
        if (!src) return false;
        if (!convert && !PyFloat_Check(src.ptr())) return false;
        value = value_type(PyFloat_AsDouble(src.ptr()));
        return true;
    }

    static handle cast(const value_type &src, return_value_policy /* policy */, handle /* parent */)
    {
        return PyFloat_FromDouble(src.template to<double>());
    }
};

} // namespace detail
} // namespace pybind11