#pragma once

#include <stdint.h>

#include <atomic>
#include <concepts>
#include <memory>
#include <optional>
#include <string>
#include <variant>
#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/typing.h>

#include "wpi/tunables/Tunable.hpp"
#include "wpystruct.h"

namespace pybind11::detail {

template <>
struct type_caster<
    std::optional<pybind11::typing::Type<pybind11::object>>>
    : optional_caster<
          std::optional<pybind11::typing::Type<pybind11::object>>> {
  bool load(handle src, bool) {
    if (!src) {
      return false;
    }
    if (src.is_none()) {
      return true;
    }
    value.emplace(pybind11::reinterpret_borrow<
                  pybind11::typing::Type<pybind11::object>>(src));
    return true;
  }
};

}  // namespace pybind11::detail

namespace wpi::tunables::python {

class PyMutationList;

class PyTunable : public std::enable_shared_from_this<PyTunable> {
 public:
  using Getter = pybind11::typing::Callable<pybind11::object()>;
  using Setter =
      pybind11::typing::Callable<void(pybind11::object)>;
  using TuneCallback =
      pybind11::typing::Callable<void(pybind11::object)>;
  using PythonType = pybind11::typing::Type<pybind11::object>;
  using Properties =
      pybind11::typing::Dict<pybind11::str, pybind11::object>;

  PyTunable(pybind11::object value,
            std::optional<Getter> getter = std::nullopt,
            std::optional<Setter> setter = std::nullopt,
            std::optional<TuneCallback> onTune = std::nullopt,
            bool robust = false, bool isMutable = true,
            std::optional<PythonType> valueType = std::nullopt,
            std::optional<PythonType> elementType = std::nullopt,
            std::optional<Properties> properties = std::nullopt,
            std::string typeString = "", bool alwaysGet = false,
            bool narrowScalar = false);

  wpi::tunables::detail::TunableBase& GetBase();

  pybind11::object Get() const;
  void Set(pybind11::object value);
  pybind11::object Mutate();

  void Refresh();
  bool NeedsRefresh() const;

 private:
  friend class PyMutationList;

  using TunableVariant =
      std::variant<wpi::tunables::TunableBool,
                   wpi::tunables::TunableInt32,
                   wpi::tunables::TunableInt64,
                   wpi::tunables::TunableFloat,
                   wpi::tunables::TunableDouble,
                   wpi::tunables::TunableString,
                   wpi::tunables::TunableRaw,
                   wpi::tunables::TunableBoolVector,
                   wpi::tunables::TunableInt64Vector,
                   wpi::tunables::TunableDoubleVector,
                   wpi::tunables::TunableStringVector,
                   wpi::tunables::Tunable<WPyStruct, WPyStructInfo>,
                   wpi::tunables::Tunable<std::vector<WPyStruct>,
                                           WPyStructInfo>>;

  template <typename T>
  static bool CachedValuesEqual(const T& lhs, const T& rhs);

  template <typename T>
  static constexpr bool IsStructCachedValue =
      std::same_as<T, WPyStruct> ||
      std::same_as<T, std::vector<WPyStruct>>;

  static std::vector<uint8_t> PackStructValue(const WPyStruct& value,
                                               const WPyStructInfo& info);

  template <typename T>
  static std::optional<std::vector<uint8_t>> PackStructData(const T&);

  static std::optional<std::vector<uint8_t>> PackStructData(
      const WPyStruct& value);
  static std::optional<std::vector<uint8_t>> PackStructData(
      const std::vector<WPyStruct>& values);

  template <typename T>
  static T ToCachedValue(pybind11::handle value);

  pybind11::object GetCached() const;
  pybind11::object MutateCached();
  void SetCached(pybind11::handle value);
  void SetCachedIfChanged(pybind11::handle value);
  std::optional<std::vector<uint8_t>> PackCachedStructData() const;

  wpi::tunables::TunableConfig MakeConfig(
      bool robust, bool isMutable,
      const std::optional<Properties>& properties, std::string typeString,
      bool alwaysGet);
  TunableVariant MakeValue(
      pybind11::handle value, bool robust, bool isMutable,
      const std::optional<PythonType>& valueType,
      const std::optional<PythonType>& elementType,
      const std::optional<Properties>& properties, std::string typeString,
      bool alwaysGet, bool narrowScalar);

  std::optional<Getter> m_getter;
  std::optional<Setter> m_setter;
  std::optional<TuneCallback> m_onTune;
  std::shared_ptr<std::atomic<std::weak_ptr<PyTunable>>> m_callbackOwner;
  TunableVariant m_value;
  std::optional<std::vector<uint8_t>> m_lastStructData;
};

}  // namespace wpi::tunables::python
