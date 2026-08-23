#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <string_view>

#include <pybind11/pybind11.h>

#include "PyTunableTable.h"

namespace wpi::tunables::python {

wpi::tunables::TunableTable GetTable(std::string_view name = "");

bool Publish(std::string_view name, pybind11::object value);

std::shared_ptr<PyTunable> Add(
    std::string_view name, pybind11::object value,
    std::optional<table::PythonType> valueType = std::nullopt,
    std::optional<table::PythonType> elementType = std::nullopt,
    bool robust = false, bool isMutable = true,
    std::optional<table::TuneCallback> onTune = std::nullopt,
    std::optional<table::Properties> properties = std::nullopt,
    std::string typeString = "");

std::shared_ptr<PyTunable> AddBoolean(
    std::string_view name, bool value, bool robust = false,
    bool isMutable = true,
    std::optional<table::TypedTuneCallback<table::BoolCallbackValue>> onTune =
        std::nullopt,
    std::optional<table::Properties> properties = std::nullopt,
    std::string typeString = "");

std::shared_ptr<PyTunable> AddInt(
    std::string_view name, std::int32_t value, bool robust = false,
    bool isMutable = true,
    std::optional<table::TypedTuneCallback<table::IntCallbackValue>> onTune =
        std::nullopt,
    std::optional<table::Properties> properties = std::nullopt,
    std::string typeString = "");

std::shared_ptr<PyTunable> AddLong(
    std::string_view name, std::int64_t value, bool robust = false,
    bool isMutable = true,
    std::optional<table::TypedTuneCallback<table::IntCallbackValue>> onTune =
        std::nullopt,
    std::optional<table::Properties> properties = std::nullopt,
    std::string typeString = "");

std::shared_ptr<PyTunable> AddFloat(
    std::string_view name, float value, bool robust = false,
    bool isMutable = true,
    std::optional<table::TypedTuneCallback<table::FloatCallbackValue>> onTune =
        std::nullopt,
    std::optional<table::Properties> properties = std::nullopt,
    std::string typeString = "");

std::shared_ptr<PyTunable> AddDouble(
    std::string_view name, double value, bool robust = false,
    bool isMutable = true,
    std::optional<table::TypedTuneCallback<table::FloatCallbackValue>> onTune =
        std::nullopt,
    std::optional<table::Properties> properties = std::nullopt,
    std::string typeString = "");

void Remove(std::string_view name);

}  // namespace wpi::tunables::python
