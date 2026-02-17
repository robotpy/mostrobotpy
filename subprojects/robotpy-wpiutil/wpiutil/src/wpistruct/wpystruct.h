
#pragma once

#include <functional>
#include <memory>
#include <string_view>

#include <fmt/format.h>
#include <wpi/struct/Struct.h>

#include <nanobind/ndarray.h>
#include <nanobind/stl/function.h>
#include <semiwrap.h>

static inline std::string pytypename(const nb::handle o) {
  auto t = nb::borrow<nb::type_object>(o);
  return ((PyTypeObject *)t.ptr())->tp_name;
}

//
// Dynamic struct + type caster
//

// This merely holds the python object being operated on, the actual
// serialization work is done in WPyStructConverter
struct WPyStruct {

  WPyStruct() = default;

  WPyStruct(const WPyStruct &other) {
    nb::gil_scoped_acquire gil;
    py = other.py;
  }

  WPyStruct &operator=(const WPyStruct &other) {
    {
      nb::gil_scoped_acquire gil;
      py = other.py;
    }
    return *this;
  }

  WPyStruct(WPyStruct &&) = default;

  WPyStruct(const nb::object &py) : py(py) {}

  ~WPyStruct() {
    nb::gil_scoped_acquire gil;
    py.release().dec_ref();
  }

  nb::object py;
};

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <> struct type_caster<WPyStruct> {
  // TODO: wpiutil.struct.T/TV?
  NB_TYPE_CASTER(WPyStruct, const_name("object"));

  bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept {
    // TODO: validation?
    value.py = borrow<object>(src);
    return true;
  }

  static handle from_cpp(const WPyStruct &src, rv_policy policy, cleanup_list *cleanup) noexcept {
    handle v = src.py;
    v.inc_ref();
    return v;
  }
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)

//
// Struct info class implementation
//

// two types of converters: static C++ converter, and dynamic python converter
struct WPyStructConverter {
  virtual ~WPyStructConverter() = default;
  virtual std::string_view GetTypeName() const = 0;

  virtual size_t GetSize() const = 0;

  virtual std::string_view GetSchema() const = 0;

  virtual void Pack(std::span<uint8_t> data, const WPyStruct &value) const = 0;

  virtual WPyStruct Unpack(std::span<const uint8_t> data) const = 0;

  // virtual void UnpackInto(WPyStruct *pyv,
  //                         std::span<const uint8_t> data) const = 0;

  virtual void ForEachNested(
      const std::function<void(std::string_view, std::string_view)> &fn)
      const = 0;
};

// static C++ converter
template <typename T> struct WPyStructCppConverter : WPyStructConverter {
  std::string_view GetTypeName() const override {
    return wpi::Struct<T>::GetTypeName();
  }

  size_t GetSize() const override { return wpi::Struct<T>::GetSize(); }

  std::string_view GetSchema() const override {
    return wpi::Struct<T>::GetSchema();
  }

  void Pack(std::span<uint8_t> data, const WPyStruct &value) const override {
    nb::gil_scoped_acquire gil;
    const T &v = nb::cast<const T&>(value.py);
    wpi::Struct<T>::Pack(data, v);
  }

  WPyStruct Unpack(std::span<const uint8_t> data) const override {
    nb::gil_scoped_acquire gil;
    return WPyStruct{nb::cast(wpi::UnpackStruct<T>(data))};
  }

  // void UnpackInto(WPyStruct *pyv,
  //                 std::span<const uint8_t> data) const override {
  //   nb::gil_scoped_acquire gil;
  //   T *v = pyv->py.cast<T *>();
  //   wpi::UnpackStructInto(v, data);
  // }

  void ForEachNested(
      const std::function<void(std::string_view, std::string_view)> &fn)
      const override {
    if constexpr (wpi::HasNestedStruct<T>) {
      wpi::Struct<T>::ForEachNested(fn);
    }
  }
};

template <typename T> void SetupWPyStruct(auto pycls) {

  auto *sptr =
      new std::shared_ptr<WPyStructConverter>(new WPyStructCppConverter<T>());

  nb::capsule c(sptr, "WPyStruct", [](void *ptr) noexcept {
    delete (std::shared_ptr<WPyStructConverter> *)ptr;
  });

  pycls.def_prop_ro_static("WPIStruct",
                                     [c](nb::object pycls) { return c; });
}

// dynamic python converter
struct WPyStructPyConverter : WPyStructConverter {

  WPyStructPyConverter(nb::object o) {
    m_typename = nb::cast<std::string>(o.attr("typename"));
    m_schema = nb::cast<std::string>(o.attr("schema"));
    m_size = nb::cast<size_t>(o.attr("size"));

    m_pack = nb::borrow<nb::callable>(o.attr("pack"));
    m_packInto = nb::borrow<nb::callable>(o.attr("packInto"));
    m_unpack = nb::borrow<nb::callable>(o.attr("unpack"));
    // m_unpackInto = nb::borrow<nb::callable>(o.attr("unpackInto"));
    m_forEachNested = nb::borrow<nb::callable>(o.attr("forEachNested"));
  }

  // copy all the relevant attributes locally
  std::string m_typename;
  std::string m_schema;
  size_t m_size;

  nb::callable m_pack;
  nb::callable m_packInto;
  nb::callable m_unpack;
  // nb::callable m_unpackInto;
  nb::callable m_forEachNested; // might be none

  std::string_view GetTypeName() const override { return m_typename; }

  size_t GetSize() const override { return m_size; }

  std::string_view GetSchema() const override { return m_schema; }

  void Pack(std::span<uint8_t> data, const WPyStruct &value) const override {
    nb::gil_scoped_acquire gil;
    nb::bytes result(m_pack(value.py));
    auto rsize = result.size();
    if (rsize != data.size()) {
      std::string msg = fmt::format(
          "{} pack did not return {} bytes (returned {})",
          pytypename(value.py.type()), data.size(), rsize);
      throw nb::value_error(msg.c_str());
    }

    memcpy(data.data(), result.data(), rsize);
  }

  WPyStruct Unpack(std::span<const uint8_t> data) const override {
    nb::gil_scoped_acquire gil;
    auto view = nb::ndarray<const uint8_t, nb::memview, nb::shape<-1>, nb::c_contig>(data.data(), {data.size()});
    return WPyStruct(m_unpack(view));
  }

  // void UnpackInto(WPyStruct *pyv,
  //                 std::span<const uint8_t> data) const override {
  //   nb::gil_scoped_acquire gil;
  //   auto view =
  //       nb::memoryview::from_memory((const void *)data.data(), data.size());
  //   m_unpackInto(pyv->py, view);
  // }

  void ForEachNested(
      const std::function<void(std::string_view, std::string_view)> &fn)
      const override {
    nb::gil_scoped_acquire gil;
    if (!m_forEachNested.is_none()) {
      m_forEachNested(fn);
    }
  }
};

// passed as I... to the wpi::Struct methods
struct WPyStructInfo {
  WPyStructInfo() = default;
  WPyStructInfo(const nb::type_object &t) {
    if (!nb::hasattr(t, "WPIStruct")) {
      auto msg = fmt::format("{} is not struct serializable (does not have WPIStruct)", pytypename(t));
      throw nb::type_error(msg.c_str());
    }

    nb::object s = t.attr("WPIStruct");

    // C++ version
    void *c = PyCapsule_GetPointer(s.ptr(), "WPyStruct");
    if (c != NULL) {
      cvt = *(std::shared_ptr<WPyStructConverter> *)c;
      return;
    }

    PyErr_Clear();

    // Python version
    try {
      cvt = std::make_shared<WPyStructPyConverter>(s);
    } catch (nb::python_error &e) {
      std::string msg = fmt::format(
          "{} is not struct serializable (invalid WPIStruct)", pytypename(t));
      nb::raise_from(e, PyExc_TypeError, msg.c_str());
      throw nb::python_error();
    }
  }

  WPyStructInfo(const WPyStruct &v) : WPyStructInfo(nb::borrow<nb::type_object>(v.py.type())) {}

  const WPyStructConverter* operator->() const {
    const auto *c = cvt.get();
    if (c == nullptr) {
      // TODO: would be nice to have a better error here, but we don't have
      // a good way to know our current context
      throw nb::value_error("Object is closed");
    }
    return c;
  }

private:
  // holds something used to do serialization
  std::shared_ptr<WPyStructConverter> cvt;
};

// Leverages the converter stored in WPyStructInfo to do the actual work
template <> struct wpi::Struct<WPyStruct, WPyStructInfo> {
  static std::string_view GetTypeName(const WPyStructInfo &info) {
    return info->GetTypeName();
  }

  static size_t GetSize(const WPyStructInfo &info) {
    return info->GetSize();
  }

  static std::string_view GetSchema(const WPyStructInfo &info) {
    return info->GetSchema();
  }

  static WPyStruct Unpack(std::span<const uint8_t> data,
                          const WPyStructInfo &info) {
    return info->Unpack(data);
  }

  // static void UnpackInto(WPyStruct *v, std::span<const uint8_t> data,
  //                        const WPyStructInfo &info) {
  //   info->UnpackInto(v, data);
  // }

  static void Pack(std::span<uint8_t> data, const WPyStruct &value,
                   const WPyStructInfo &info) {
    info->Pack(data, value);
  }

  static void
  ForEachNested(std::invocable<std::string_view, std::string_view> auto fn,
                const WPyStructInfo &info) {
    info->ForEachNested(fn);
  }
};

static_assert(wpi::StructSerializable<WPyStruct, WPyStructInfo>);
static_assert(wpi::HasNestedStruct<WPyStruct, WPyStructInfo>);

// This breaks on readonly structs, so we disable for now
// static_assert(wpi::MutableStructSerializable<WPyStruct, WPyStructInfo>);
