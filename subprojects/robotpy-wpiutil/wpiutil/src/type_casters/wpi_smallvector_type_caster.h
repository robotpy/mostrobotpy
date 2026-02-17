
#pragma once

#include <nanobind/nanobind.h>
#include <nanobind/stl/detail/nb_list.h>

#include <wpi/SmallVector.h>

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <typename Type, unsigned Size> struct type_caster<wpi::SmallVector<Type, Size>>
 : list_caster<wpi::SmallVector<Type, Size>, Type> { };

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)
