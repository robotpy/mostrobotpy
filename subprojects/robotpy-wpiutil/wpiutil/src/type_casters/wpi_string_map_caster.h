
#pragma once

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/detail/nb_dict.h>

#include <wpi/StringMap.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename Value>
struct type_caster<wpi::StringMap<Value>>
 : dict_caster<wpi::StringMap<Value>, std::string, Value> { };

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)
