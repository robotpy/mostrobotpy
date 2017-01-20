
#include <pybind11/pybind11.h>


namespace pybind11 { namespace detail {
    
template <> struct type_caster<llvm::StringRef> {
public:
    
    PYBIND11_TYPE_CASTER(llvm::StringRef, _("str"));
    
    bool load(handle src, bool) {
        std::string s = py::cast<std::string>(src);
        value = llvm::StringRef(s);
        return true;
    }
    
    static handle cast(const llvm::StringRef &s, return_value_policy, handle defval) {
        return py::str((std::string)s);
    }
};
    
    
}} // namespace pybind11::detail
