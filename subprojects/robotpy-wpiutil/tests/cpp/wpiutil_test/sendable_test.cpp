
#include <robotpy_build.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <wpi/sendable/SendableBuilder.h>
#include <wpi/sendable/SendableRegistry.h>

class MySendableBuilder : public wpi::SendableBuilder {
public:
  MySendableBuilder(py::dict keys) : keys(keys) {}

  ~MySendableBuilder() {
    // leak this so the python interpreter doesn't crash on shutdown
    keys.release();
  }

  void SetSmartDashboardType(std::string_view type) override {}

  void SetActuator(bool value) override {}

  void SetSafeState(std::function<void()> func) override {}

  void AddBooleanProperty(std::string_view key, std::function<bool()> getter,
                          std::function<void(bool)> setter) override {}

  void AddIntegerProperty(std::string_view key, std::function<int64_t()> getter,
                          std::function<void(int64_t)> setter) override {}

  void AddFloatProperty(std::string_view key, std::function<float()> getter,
                        std::function<void(float)> setter) override {}

  void AddDoubleProperty(std::string_view key, std::function<double()> getter,
                         std::function<void(double)> setter) override {
    py::gil_scoped_acquire gil;
    py::object pykey = py::cast(key);
    keys[pykey] = std::make_tuple(getter, setter);
  }

  void
  AddStringProperty(std::string_view key, std::function<std::string()> getter,
                    std::function<void(std::string_view)> setter) override {}

  void AddBooleanArrayProperty(
      std::string_view key, std::function<std::vector<int>()> getter,
      std::function<void(std::span<const int>)> setter) override {}

  void AddIntegerArrayProperty(
      std::string_view key, std::function<std::vector<int64_t>()> getter,
      std::function<void(std::span<const int64_t>)> setter) override {}

  void AddFloatArrayProperty(
      std::string_view key, std::function<std::vector<float>()> getter,
      std::function<void(std::span<const float>)> setter) override {}

  void AddDoubleArrayProperty(
      std::string_view key, std::function<std::vector<double>()> getter,
      std::function<void(std::span<const double>)> setter) override {}

  void AddStringArrayProperty(
      std::string_view key, std::function<std::vector<std::string>()> getter,
      std::function<void(std::span<const std::string>)> setter) override {}

  void AddRawProperty(
      std::string_view key, std::string_view typeString,
      std::function<std::vector<uint8_t>()> getter,
      std::function<void(std::span<const uint8_t>)> setter) override {}

  void AddSmallStringProperty(
      std::string_view key,
      std::function<std::string_view(wpi::SmallVectorImpl<char> &buf)> getter,
      std::function<void(std::string_view)> setter) override {}

  void AddSmallBooleanArrayProperty(
      std::string_view key,
      std::function<std::span<const int>(wpi::SmallVectorImpl<int> &buf)>
          getter,
      std::function<void(std::span<const int>)> setter) override {}

  void AddSmallIntegerArrayProperty(
      std::string_view key,
      std::function<
          std::span<const int64_t>(wpi::SmallVectorImpl<int64_t> &buf)>
          getter,
      std::function<void(std::span<const int64_t>)> setter) override {}

  void AddSmallFloatArrayProperty(
      std::string_view key,
      std::function<std::span<const float>(wpi::SmallVectorImpl<float> &buf)>
          getter,
      std::function<void(std::span<const float>)> setter) override {}

  void AddSmallDoubleArrayProperty(
      std::string_view key,
      std::function<std::span<const double>(wpi::SmallVectorImpl<double> &buf)>
          getter,
      std::function<void(std::span<const double>)> setter) override {}

  void AddSmallStringArrayProperty(
      std::string_view key,
      std::function<
          std::span<const std::string>(wpi::SmallVectorImpl<std::string> &buf)>
          getter,
      std::function<void(std::span<const std::string>)> setter) override {}

  void AddSmallRawProperty(
      std::string_view key, std::string_view typeString,
      std::function<std::span<uint8_t>(wpi::SmallVectorImpl<uint8_t> &buf)>
          getter,
      std::function<void(std::span<const uint8_t>)> setter) override {}

  wpi::SendableBuilder::BackendKind GetBackendKind() const override {
    return wpi::SendableBuilder::BackendKind::kUnknown;
  }

  bool IsPublished() const override { return false; }
  void Update() override {}
  void ClearProperties() override {}

  py::dict keys;
};

void Publish(wpi::SendableRegistry::UID sendableUid, py::dict keys) {
  auto builder = std::make_unique<MySendableBuilder>(keys);
  wpi::SendableRegistry::Publish(sendableUid, std::move(builder));
}

void sendable_test(py::module &m) { m.def("publish", Publish); }