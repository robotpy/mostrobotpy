#pragma once

#include <memory>
#include <string>
#include <string_view>

#include <pybind11/pybind11.h>

namespace wpi::tunables {

class TunableTable;

namespace python {

class PyComplexTunableAdapter;
class PyTunable;

void InitializeTunablePython(pybind11::module_& module);
void RegisterPreUpdateCallback();
void CleanupPythonStorage();
void ClearValues();
void StoreRefreshValue(std::string_view path,
                       const std::shared_ptr<PyTunable>& tunable);
void RemoveRefreshPath(std::string_view path);
void RemoveRetainedPath(std::string_view path);
void RemovePath(std::string_view path);
void RemoveValue(pybind11::handle value);
std::string NormalizePath(std::string_view path);
std::string NormalizeTablePath(const wpi::tunables::TunableTable& table,
                               std::string_view name);

void RetainValue(std::string path, std::shared_ptr<PyTunable> value);
void RetainComplex(std::string path,
                   std::shared_ptr<PyComplexTunableAdapter> value);
void RetainNativeComplex(std::string path, pybind11::object value);

}  // namespace python
}  // namespace wpi::tunables
