#pragma once

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <wpi/array.h>

namespace pybind11 {
namespace detail {

template <typename Type, size_t Size>
struct type_caster<wpi::array<Type, Size>> {
  using value_conv = make_caster<Type>;

  // Have to copy/paste PYBIND11_TYPE_CASTER implementation because wpi::array
  // is not default constructable
  //
  // begin PYBIND11_TYPE_CASTER
protected:
  wpi::array<Type, Size> value{wpi::empty_array_t{}};

public:
  static constexpr auto name = _("Tuple[") + value_conv::name + _("]");
  template <
      typename T_,
      enable_if_t<std::is_same<wpi::array<Type, Size>, remove_cv_t<T_>>::value,
                  int> = 0>
  static handle cast(T_ *src, return_value_policy policy, handle parent) {
    if (!src)
      return none().release();
    if (policy == return_value_policy::take_ownership) {
      auto h = cast(std::move(*src), policy, parent);
      delete src;
      return h;
    } else {
      return cast(*src, policy, parent);
    }
  }
  operator wpi::array<Type, Size> *() { return &value; }
  operator wpi::array<Type, Size> &() { return value; }
  operator wpi::array<Type, Size> &&() && { return std::move(value); }
  template <typename T_>
  using cast_op_type = pybind11::detail::movable_cast_op_type<T_>;
  // end PYBIND11_TYPE_CASTER

  bool load(handle src, bool convert) {
    if (!isinstance<sequence>(src))
      return false;
    auto l = reinterpret_borrow<sequence>(src);
    if (l.size() != Size)
      return false;
    size_t ctr = 0;
    for (auto it : l) {
      value_conv conv;
      if (!conv.load(it, convert))
        return false;
      value[ctr++] = cast_op<Type &&>(std::move(conv));
    }
    return true;
  }

  template <typename T>
  static handle cast(T &&src, return_value_policy policy, handle parent) {
    tuple l(src.size());
    size_t index = 0;
    for (auto &&value : src) {
      auto value_ = reinterpret_steal<object>(
          value_conv::cast(forward_like<T>(value), policy, parent));
      if (!value_)
        return handle();
      PyTuple_SET_ITEM(l.ptr(), (ssize_t)index++,
                       value_.release().ptr()); // steals a reference
    }
    return l.release();
  }
};

} // namespace detail
} // namespace pybind11