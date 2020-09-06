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
PYBIND_UNIT_NAME(microsecond, microseconds);
PYBIND_UNIT_NAME(nanosecond, nanoseconds);
PYBIND_UNIT_NAME(meter, meters);
PYBIND_UNIT_NAME(foot, feet);
PYBIND_UNIT_NAME(meters_per_second, meters_per_second);
PYBIND_UNIT_NAME(meters_per_second_squared, meters_per_second_squared);
PYBIND_UNIT_NAME(feet_per_second, feet_per_second);
PYBIND_UNIT_NAME(feet_per_second_squared, feet_per_second_squared);
PYBIND_UNIT_NAME(degree, degrees);
PYBIND_UNIT_NAME(degrees_per_second, degrees_per_second);
PYBIND_UNIT_NAME(radian, radians);
PYBIND_UNIT_NAME(radians_per_second, radians_per_second);
PYBIND_UNIT_NAME(volt, volts);
PYBIND_UNIT_NAME(turn, turns);

PYBIND_UNIT_NAME(dimensionless::scalar, float);

#undef PYBIND_UNIT_NAME

template <>
struct handle_type_name<units::unit_t<units::inverse<units::seconds>>> {
    static constexpr auto name = _("units_per_second");
};

template <>
struct handle_type_name<
    units::unit_t<units::inverse<units::squared<units::seconds>>>
> {
    static constexpr auto name = _("units_per_second_squared");
};

template <>
struct handle_type_name<units::unit_t<units::compound_unit<
    units::radians_per_second,
    units::inverse<units::seconds>
>>> {
    static constexpr auto name = _("radians_per_second_squared");
};

using volt_seconds = units::compound_unit<units::volts, units::seconds>;
using volt_seconds_squared = units::compound_unit<volt_seconds, units::seconds>;

template <>
struct handle_type_name<units::unit_t<volt_seconds>> {
    static constexpr auto name = _("volt_seconds");
};

template <>
struct handle_type_name<units::unit_t<volt_seconds_squared>> {
    static constexpr auto name = _("volt_seconds_squared");
};

#define PYBIND_FF_UNITS(unit_name)  \
template <> struct handle_type_name<units::unit_t<units::compound_unit<volt_seconds, units::inverse<units::unit_name>>>> \
{ static constexpr auto name = _("volt_seconds_per_" #unit_name); }; \
template <> struct handle_type_name<units::unit_t<units::compound_unit<volt_seconds_squared, units::inverse<units::unit_name>>>> \
{ static constexpr auto name = _("volt_seconds_squared_per_" #unit_name); }

PYBIND_FF_UNITS(meter);
PYBIND_FF_UNITS(feet);
PYBIND_FF_UNITS(radian);

#undef PYBIND_FF_UNITS

template <>
struct handle_type_name<units::unit_t<units::compound_unit<
    units::radian,
    units::inverse<units::meter>
>>> {
    static constexpr auto name = _("radians_per_meter");
};

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
