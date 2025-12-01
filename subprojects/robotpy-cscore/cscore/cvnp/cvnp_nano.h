#pragma once
#include <iostream>
#include <opencv2/core/core.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/ndarray.h>

namespace cvnp_nano
{
    nanobind::ndarray<> mat_to_nparray(const cv::Mat &m, nanobind::handle owner);
    cv::Mat nparray_to_mat(nanobind::ndarray<> &a, nanobind::handle owner);

    template <typename _Tp>
    cv::Mat_<_Tp> nparray_to_mat_typed(nanobind::ndarray<> &a, nanobind::handle owner) {
        cv::Mat mat = nparray_to_mat(a, owner);
        return mat;  // Convert to Mat_<_Tp>
    }

    void                      print_types_synonyms();
}

//#define DEBUG_CVNP(x) std::cout << "DEBUG_CVNP: " << x << std::endl;
#define DEBUG_CVNP(x)


NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

//
// Type caster for cv::Mat
// ========================
template <>
struct type_caster<cv::Mat>
{
    NB_TYPE_CASTER(cv::Mat, const_name("numpy.array"))

    bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept
    {
        DEBUG_CVNP("Enter from_python Type caster for cv::Mat");
        if (!isinstance<ndarray<>>(src))
        {
            PyErr_WarnFormat(PyExc_Warning, 1, "cvnp_nano: cv::Mat type_caster from_python: expected a numpy.ndarray");
            return false;
        }
        try
        {
            auto a = nanobind::cast<ndarray<>>(src);

            // Create a capsule that keeps the Python ndarray alive as long as cv::Mat needs it
            nanobind::object capsule_owner = nanobind::capsule(src.ptr(), [](void* p) noexcept {
                Py_XDECREF(reinterpret_cast<PyObject*>(p));  // Decrement reference count of ndarray when capsule is destroyed
            });
            Py_INCREF(src.ptr());  // Increment reference to ensure ndarray is not prematurely garbage collected


            this->value = cvnp_nano::nparray_to_mat(a, capsule_owner);
            DEBUG_CVNP("Leave from_python Type caster for cv::Mat");
            return true;
        }
        catch (const std::exception& e)
        {
            PyErr_WarnFormat(PyExc_Warning, 1, "cvnp_nano: cv::Mat type_caster from_python, exception: %s", e.what());
            return false;
        }
    }

    static handle from_cpp(const cv::Mat &mat, rv_policy policy, cleanup_list *cleanup) noexcept
    {
        DEBUG_CVNP("Enter from_cpp Type caster for cv::Mat");

        try
        {
            // Set default policies if automatic
            if (policy == rv_policy::automatic)
                policy = rv_policy::copy;
            else if (policy == rv_policy::automatic_reference)
                policy = rv_policy::reference;

            // Exported ndarray
            ndarray<> a;
            {
                if (policy == rv_policy::take_ownership)
                {
                    // Create a Python object that wraps the existing C++ instance and takes full ownership of it. No copies are made. Python will call the C++ destructor and delete operator when the Python wrapper is garbage collected at some later point. The C++ side must relinquish ownership and is not allowed to destruct the instance, or undefined behavior will ensue
                    DEBUG_CVNP("    rv_policy::take_ownership => capsule takes ownership");
                    // Warning: the capsule will delete the mat which is passed as a parameter, since "the C++ side must relinquish ownership and is not allowed to destruct the instance, or undefined behavior will ensue"
                    nanobind::object owner = nanobind::capsule(&mat, [](void* p) noexcept { delete (cv::Mat*)p; });
                    a = cvnp_nano::mat_to_nparray(mat, owner);
                }
                else if (policy == rv_policy::copy)
                {
                    // Copy-construct a new Python object from the C++ instance. The new copy will be owned by Python, while C++ retains ownership of the original.
                    DEBUG_CVNP("    rv_policy::copy => copy mat on heap");
                    cv::Mat* heap_mat = new cv::Mat(mat);  // Allocate on the heap
                    // Note: the constructor cv::Mat(mat) will not copy the data, but instead increment the reference counter
                    // of `cv::Mat mat`
                    // => the python numpy array and the C++ cv::Mat will share the same data
                    nanobind::object owner = nanobind::capsule(heap_mat, [](void* p) noexcept { delete (cv::Mat*)p; });
                    a = cvnp_nano::mat_to_nparray(*heap_mat, owner);
                }
                else if (policy == rv_policy::move)
                {
                    // Move-construct a new Python object from the C++ instance. The new object will be owned by Python, while C++ retains ownership of the original (whose contents were likely invalidated by the move operation).

                    // move is implemented as rv_policy::copy (because OpenCV's Mat already has a reference counter)
                    DEBUG_CVNP("    rv_policy::move => copy mat on heap (not a real move)");
                    cv::Mat* heap_mat = new cv::Mat(mat);  // Allocate on the heap (this is not a move per se)
                    // => the python numpy array and the C++ cv::Mat will share the same data
                    nanobind::object owner = nanobind::capsule(heap_mat, [](void* p) noexcept { delete (cv::Mat*)p; });
                    a = cvnp_nano::mat_to_nparray(*heap_mat, owner);
                }
                else if (policy == rv_policy::reference)
                {
                    // Create a Python object that wraps the existing C++ instance without taking ownership of it. No copies are made. Python will never call the destructor or delete operator, even when the Python wrapper is garbage collected.
                    DEBUG_CVNP("    rv_policy::reference => using no_owner");
                    nanobind::handle no_owner = {};
                    a = cvnp_nano::mat_to_nparray(mat, no_owner);
                }
                else if (policy == rv_policy::reference_internal)
                {
                    // A safe extension of the reference policy for methods that implement some form of attribute access. It creates a Python object that wraps the existing C++ instance without taking ownership of it. Additionally, it adjusts reference counts to keeps the method’s implicit self argument alive until the newly created object has been garbage collected.
                    DEBUG_CVNP("    rv_policy::reference_internal => using no_owner");
                    nanobind::handle no_owner = {};
                    a = cvnp_nano::mat_to_nparray(mat, no_owner);
                }
                else if (policy == rv_policy::none)
                {
                    // This is the most conservative policy: it simply refuses the cast unless the C++ instance already has a corresponding Python object, in which case the question of ownership becomes moot.
                    DEBUG_CVNP("    rv_policy::none => unhandled yet");
                    throw std::runtime_error("rv_policy::none not yet supported in cv::Mat caster");
                }
                else
                {
                    DEBUG_CVNP("policy received: " << (int)policy);
                    throw std::runtime_error("unexpected rv_policy in cv::Mat caster");
                }
            }

            // inspired by ndarray.h caster:
            // We need to call ndarray_export to export a python handle for the ndarray
            auto r = ndarray_export(
                a.handle(), // internal array handle
                nanobind::numpy::value, // framework (i.e numpy, pytorch, etc)
                policy,
                cleanup);

            DEBUG_CVNP("Leave from_cpp Type caster for cv::Mat");
            return r;
        }
        catch (const std::exception& e)
        {
            PyErr_WarnFormat(PyExc_Warning, 1, "nanobind: exception in MatrixFixedSize type_caster from_cpp: %s", e.what());
            return {};
        }
    }
};


//
// Type caster for cv::Mat_<_Tp>  (reuses cv::Mat caster)
// =======================================================
template <typename _Tp>
struct type_caster<cv::Mat_<_Tp>> : public type_caster<cv::Mat> // Inherit from cv::Mat caster
{
    // Adjust type_caster for Mat_<_Tp> to handle _Tp and ensure correct dtype
    NB_TYPE_CASTER(cv::Mat_<_Tp>, const_name("numpy.ndarray"))

    bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept
    {
        DEBUG_CVNP("Enter from_python Type caster for cv::Mat_<_Tp>");

        if (!isinstance<ndarray<>>(src))
        {
            PyErr_WarnFormat(PyExc_Warning, 1, "cvnp_nano: cv::Mat_<_Tp> type_caster from_python: expected a numpy.ndarray");
            return false;
        }

        try
        {
            auto a = nanobind::cast<ndarray<>>(src);

            // Check if the dtype of ndarray matches _Tp
            if (a.dtype() != nanobind::dtype<_Tp>()) {
                PyErr_WarnFormat(PyExc_Warning, 1, "cvnp_nano: dtype of ndarray does not match cv::Mat_<_Tp> type");
                return false;
            }

            // Create a capsule that keeps the Python ndarray alive as long as cv::Mat_<_Tp> needs it
            nanobind::object capsule_owner = nanobind::capsule(src.ptr(), [](void* p) noexcept {
                Py_XDECREF(reinterpret_cast<PyObject*>(p));
            });
            Py_INCREF(src.ptr());

            // Use nparray_to_mat_typed to convert ndarray to cv::Mat_<_Tp>
            this->value = cvnp_nano::nparray_to_mat_typed<_Tp>(a, capsule_owner);

            DEBUG_CVNP("Leave from_python Type caster for cv::Mat_<_Tp>");
            return true;
        }
        catch (const std::exception& e)
        {
            PyErr_WarnFormat(PyExc_Warning, 1, "cvnp_nano: cv::Mat_<_Tp> type_caster from_python, exception: %s", e.what());
            return false;
        }
    }

    static handle from_cpp(const cv::Mat_<_Tp> &mat, rv_policy policy, cleanup_list *cleanup) noexcept
    {
        DEBUG_CVNP("Enter from_cpp Type caster for cv::Mat_<_Tp>");

        try
        {
            // Call the base cv::Mat type_caster's from_cpp method
            return type_caster<cv::Mat>::from_cpp(mat, policy, cleanup);
        }
        catch (const std::exception& e)
        {
            PyErr_WarnFormat(PyExc_Warning, 1, "cvnp_nano: cv::Mat_<_Tp> type_caster from_cpp, exception: %s", e.what());
            return {};
        }
    }
};


// Type caster for cv::Vec
// =======================
template <typename _Tp, int cn>
struct type_caster<cv::Vec<_Tp, cn>>
{
    using VecTp = cv::Vec<_Tp, cn>;
    using ScalarTp = _Tp;
    static constexpr size_t size = cn;

    NB_TYPE_CASTER(VecTp, const_name("list"));

    // Conversion from Python to C++ (sequence (list|tuple|array) -> cv::Vec)
    bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept {
        DEBUG_CVNP("Enter from_python Type caster for cv::Vec");

        // 1) Check for Python sequence-ness
        if (!PySequence_Check(src.ptr())) {
            PyErr_SetString(PyExc_TypeError, "Expected a sequence to convert to cv::Vec.");
            return false;
        }

        // 2) Get sequence size
        Py_ssize_t len = PySequence_Size(src.ptr());
        if (len != size) {
            PyErr_SetString(PyExc_ValueError, "Wrong number of elements to convert to cv::Vec.");
            return false;
        }

        // 3) Extract each element
        try {
            for (Py_ssize_t i = 0; i < len; i++) {
                // GetItem() returns a new reference; wrap it in nanobind::steal
                nanobind::object item = nanobind::steal(
                    PySequence_GetItem(src.ptr(), i));
                // Cast the item to your scalar type and store it
                value[i] = nanobind::cast<ScalarTp>(item);
            }
            DEBUG_CVNP("Leave from_python Type caster for cv::Vec");
            return true;
        } catch (const std::exception &e) {
            PyErr_SetString(PyExc_ValueError, e.what());
            return false;
        }
    }

    // Conversion from C++ to Python (cv::Vec -> list)
    static handle from_cpp(const VecTp &value, rv_policy policy, cleanup_list *cleanup) noexcept {
        DEBUG_CVNP("Enter from_cpp Type caster for cv::Vec");
        nanobind::list as_list;
        for (size_t i = 0; i < size; ++i) {
            as_list.append(value[i]);
        }
        DEBUG_CVNP("Leave from_cpp Type caster for cv::Vec");
        return as_list.release();
    }
};


// Type caster for cv::Matx
// ========================
template <typename _Tp, int m, int n>
struct type_caster<cv::Matx<_Tp, m, n>>
{
    using MatxTp = cv::Matx<_Tp, m, n>;
    using ScalarTp = _Tp;
    static constexpr size_t rows = m;
    static constexpr size_t cols = n;

    NB_TYPE_CASTER(MatxTp, const_name("list_of_list"));

    // Conversion from Python to C++ (sequence-of-sequences -> cv::Matx)
    bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept {
        if (!PySequence_Check(src.ptr())) {
            PyErr_SetString(PyExc_TypeError, "Expected a sequence to convert to cv::Matx.");
            return false;
        }

        Py_ssize_t outer_len = PySequence_Size(src.ptr());
        if (outer_len != rows) {
            PyErr_SetString(PyExc_ValueError, "Wrong number of rows to convert to cv::Matx.");
            return false;
        }

        try {
            // Loop over the outer dimension
            for (Py_ssize_t i = 0; i < outer_len; i++) {
                nanobind::object row = nanobind::steal(PySequence_GetItem(src.ptr(), i));

                // Check each row
                if (!PySequence_Check(row.ptr())) {
                    PyErr_SetString(PyExc_TypeError, "Expected each row to be a sequence.");
                    return false;
                }

                Py_ssize_t inner_len = PySequence_Size(row.ptr());
                if (inner_len != cols) {
                    PyErr_SetString(PyExc_ValueError, "Wrong number of columns in a row to convert to cv::Matx.");
                    return false;
                }

                // Loop over each element in the row
                for (Py_ssize_t j = 0; j < inner_len; j++) {
                    nanobind::object item = nanobind::steal(PySequence_GetItem(row.ptr(), j));
                    value(i, j) = nanobind::cast<ScalarTp>(item);
                }
            }
            return true;
        }
        catch (const std::exception &e) {
            PyErr_SetString(PyExc_ValueError, e.what());
            return false;
        }
    }

    // Conversion from C++ to Python (cv::Matx -> list-of-lists)
    static handle from_cpp(const MatxTp &value, rv_policy policy, cleanup_list *cleanup) noexcept {
        nanobind::list outer_list;

        for (size_t i = 0; i < rows; ++i) {
            nanobind::list inner_list;
            for (size_t j = 0; j < cols; ++j) {
                inner_list.append(value(i, j));
            }
            outer_list.append(inner_list);
        }
        return outer_list.release();
    }
};



// Type caster for cv::Size
// ========================
template<typename _Tp>
struct type_caster<cv::Size_<_Tp>>
{
    using SizeTp = cv::Size_<_Tp>;

    NB_TYPE_CASTER(SizeTp, const_name("tuple"));

    bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept {
        if (!PySequence_Check(src.ptr())) {
            PyErr_SetString(PyExc_TypeError, "Expected a sequence to convert to cv::Size.");
            return false;
        }

        Py_ssize_t len = PySequence_Size(src.ptr());
        if (len != 2) {
            PyErr_SetString(PyExc_ValueError, "Expected exactly 2 elements for cv::Size.");
            return false;
        }

        try {
            nanobind::object item0 = nanobind::steal(PySequence_GetItem(src.ptr(), 0));
            nanobind::object item1 = nanobind::steal(PySequence_GetItem(src.ptr(), 1));
            _Tp width  = nanobind::cast<_Tp>(item0);
            _Tp height = nanobind::cast<_Tp>(item1);
            value = cv::Size_<_Tp>(width, height);
            return true;
        } catch (const std::exception &e) {
            PyErr_SetString(PyExc_ValueError, e.what());
            return false;
        }
    }

    // Conversion part 2 (C++ -> Python, i.e., cv::Size_ -> list)
    static handle from_cpp(const SizeTp &value, rv_policy policy, cleanup_list *cleanup) noexcept {
        nanobind::list out;
        out.append(value.width);
        out.append(value.height);
        return out.release();
    }
};


// Type caster for cv::Point
// =========================
template<typename _Tp>
struct type_caster<cv::Point_<_Tp>>
{
    using PointTp = cv::Point_<_Tp>;

    NB_TYPE_CASTER(PointTp, const_name("tuple"));

    bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept {
        if (!PySequence_Check(src.ptr())) {
            PyErr_SetString(PyExc_TypeError, "Expected a sequence to convert to cv::Point.");
            return false;
        }

        Py_ssize_t len = PySequence_Size(src.ptr());
        if (len != 2) {
            PyErr_SetString(PyExc_ValueError, "Expected exactly 2 elements for cv::Point.");
            return false;
        }

        try {
            nanobind::object item0 = nanobind::steal(PySequence_GetItem(src.ptr(), 0));
            nanobind::object item1 = nanobind::steal(PySequence_GetItem(src.ptr(), 1));
            _Tp x = nanobind::cast<_Tp>(item0);
            _Tp y = nanobind::cast<_Tp>(item1);
            value = cv::Point_<_Tp>(x, y);
            return true;
        } catch (...) {
            // ...
            return false;
        }
    }

    static handle from_cpp(const PointTp &value, rv_policy policy, cleanup_list *cleanup) noexcept {
        nanobind::list out;
        out.append(value.x);
        out.append(value.y);
        return out.release();
    }

};


// Type caster for cv::Point3_
// ===========================
template<typename _Tp>
struct type_caster<cv::Point3_<_Tp>>
{
    using PointTp = cv::Point3_<_Tp>;

    NB_TYPE_CASTER(PointTp, const_name("tuple"));

    bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept {
        if (!PySequence_Check(src.ptr())) {
            PyErr_SetString(PyExc_TypeError, "Expected a sequence to convert to cv::Point3_.");
            return false;
        }

        Py_ssize_t len = PySequence_Size(src.ptr());
        if (len != 3) {
            PyErr_SetString(PyExc_ValueError, "Expected exactly 3 elements for cv::Point3_.");
            return false;
        }

        try {
            nanobind::object item0 = nanobind::steal(PySequence_GetItem(src.ptr(), 0));
            nanobind::object item1 = nanobind::steal(PySequence_GetItem(src.ptr(), 1));
            nanobind::object item2 = nanobind::steal(PySequence_GetItem(src.ptr(), 2));
            _Tp x = nanobind::cast<_Tp>(item0);
            _Tp y = nanobind::cast<_Tp>(item1);
            _Tp z = nanobind::cast<_Tp>(item2);
            value = cv::Point3_<_Tp>(x, y, z);
            return true;
        } catch (...) {
            // ...
            return false;
        }

    }

    static handle from_cpp(const PointTp &value, rv_policy policy, cleanup_list *cleanup) noexcept {
        nanobind::list out;
        out.append(value.x);
        out.append(value.y);
        out.append(value.z);
        return out.release();
    }
};


// Type caster for cv::Scalar_
// ===========================
template<typename _Tp>
struct type_caster<cv::Scalar_<_Tp>>
{
    using ScalarTp = cv::Scalar_<_Tp>;

    NB_TYPE_CASTER(ScalarTp, const_name("tuple"));

    bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept {
        if (!PySequence_Check(src.ptr())) {
            PyErr_SetString(PyExc_TypeError, "Expected a sequence to convert to cv::Scalar_.");
            return false;
        }

        Py_ssize_t len = PySequence_Size(src.ptr());
        if (len < 1 || len > 4) {
            PyErr_SetString(PyExc_ValueError, "Expected between 1 and 4 elements for cv::Scalar_.");
            return false;
        }

        try {
            // Initialize to zero
            _Tp vals[4] = { (_Tp)0, (_Tp)0, (_Tp)0, (_Tp)0 };

            for (Py_ssize_t i = 0; i < len; i++) {
                nanobind::object item = nanobind::steal(PySequence_GetItem(src.ptr(), i));
                vals[i] = nanobind::cast<_Tp>(item);
            }
            value = cv::Scalar_<_Tp>(vals[0], vals[1], vals[2], vals[3]);
            return true;
        } catch (...) {
            // ...
            return false;
        }
    }

    static handle from_cpp(const ScalarTp &value, rv_policy policy, cleanup_list *cleanup) noexcept {
        // Always return a 4-element list (OpenCV's default representation).
        nanobind::list out;
        out.append(value[0]);
        out.append(value[1]);
        out.append(value[2]);
        out.append(value[3]);
        return out.release();
    }
};


// Type caster for cv::Rect
// ========================
template<typename _Tp>
struct type_caster<cv::Rect_<_Tp>>
{
    using RectTp = cv::Rect_<_Tp>;

    NB_TYPE_CASTER(RectTp, const_name("tuple"));

    bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept {
        if (!PySequence_Check(src.ptr())) {
            PyErr_SetString(PyExc_TypeError, "Expected a sequence to convert to cv::Rect_.");
            return false;
        }

        Py_ssize_t len = PySequence_Size(src.ptr());
        if (len != 4) {
            PyErr_SetString(PyExc_ValueError, "Expected exactly 4 elements for cv::Rect_.");
            return false;
        }

        try {
            nanobind::object item0 = nanobind::steal(PySequence_GetItem(src.ptr(), 0));
            nanobind::object item1 = nanobind::steal(PySequence_GetItem(src.ptr(), 1));
            nanobind::object item2 = nanobind::steal(PySequence_GetItem(src.ptr(), 2));
            nanobind::object item3 = nanobind::steal(PySequence_GetItem(src.ptr(), 3));

            _Tp x      = nanobind::cast<_Tp>(item0);
            _Tp y      = nanobind::cast<_Tp>(item1);
            _Tp width  = nanobind::cast<_Tp>(item2);
            _Tp height = nanobind::cast<_Tp>(item3);
            value = cv::Rect_<_Tp>(x, y, width, height);
            return true;
        } catch (...) {
            // ...
            return false;
        }
    }

    static handle from_cpp(const RectTp &value, rv_policy policy, cleanup_list *cleanup) noexcept {
        nanobind::list out;
        out.append(value.x);
        out.append(value.y);
        out.append(value.width);
        out.append(value.height);
        return out.release();
    }
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)


//  ===================================================================================================================
//                    Inline implementations of cvnp_nano functions below
//  ===================================================================================================================
// suppress warning:
// cvnp_nano.cpp: warning: ‘cvnp_nano::synonyms::TypeSynonyms’ declared with greater visibility
// than the type of its field ‘cvnp_nano::synonyms::TypeSynonyms::dtype’ [-Wattributes]
#ifdef __clang__
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wattributes"
#elif defined(__GNUC__)
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wattributes"
#endif

namespace cvnp_nano
{
    namespace synonyms
    {
        // #define CVNP_NANO_DEBUG_ALLOCATOR

#ifdef CVNP_NANO_DEBUG_ALLOCATOR
        int nbAllocations = 0;
#endif
        struct TypeSynonyms
        {
            int cv_depth = -1;
            std::string cv_depth_name;
            std::string scalar_typename_;
            nanobind::dlpack::dtype dtype;

            std::string str() const;
        };

        inline std::vector<TypeSynonyms> get_type_synonyms()
        {
            return {
                {CV_8U,  "CV_8U",  "uint8",   nanobind::dtype<uint8_t>()},
                {CV_8S,  "CV_8S",  "int8",    nanobind::dtype<int8_t>()},
                {CV_16U, "CV_16U", "uint16",  nanobind::dtype<uint16_t>()},
                {CV_16S, "CV_16S", "int16",   nanobind::dtype<int16_t>()},
                {CV_32S, "CV_32S", "int32",   nanobind::dtype<int32_t>()},
                {CV_32F, "CV_32F", "float32", nanobind::dtype<float>()},
                {CV_64F, "CV_64F", "float64", nanobind::dtype<double>()},
                // Note: this format needs adaptations: float16
            };
        }



        inline std::string align_center(const std::string &s)
        {
            static int sColumnWidth = 12;
            int nb_spaces = s.size() < sColumnWidth ? sColumnWidth - s.size() : 0;
            int nb_spaces_left = nb_spaces / 2;
            int nb_spaces_right = sColumnWidth - s.size() - nb_spaces_left;
            if (nb_spaces_right < 0)
                nb_spaces_right = 0;
            return std::string((size_t) nb_spaces_left, ' ') + s + std::string((size_t) nb_spaces_right, ' ');
        }

        inline std::string align_center(const int v)
        {
            return align_center(std::to_string(v));
        }

        inline std::string TypeSynonyms::str() const
        {
            std::string dtype_str =
                std::string("code=") + std::to_string((int) dtype.code)
                + " bits=" + std::to_string(dtype.bits)
                + " lanes=" + std::to_string(dtype.lanes);
            return align_center(cv_depth) + align_center(cv_depth_name) + align_center(scalar_typename_) +
                   align_center(dtype_str);
        }


        inline std::string print_types_synonyms_str()
        {
            std::string title =
                align_center("cv_depth") + align_center("cv_depth_name")
                + align_center("np_format") + align_center("dtype_details");;

            std::string r;
            r = title + "\n";
            for (const auto &format: get_type_synonyms())
                r = r + format.str() + "\n";
            return r;
        }
    } // namespace synonyms

    namespace detail
    {
        // Helper functions for error messages
        inline std::string format_shape(const nanobind::ndarray<>& a)
        {
            std::string result = "(";
            for (size_t i = 0; i < a.ndim(); ++i)
            {
                if (i > 0) result += ", ";
                result += std::to_string(a.shape(i));
            }
            result += ")";
            return result;
        }

        inline std::string format_strides(const nanobind::ndarray<>& a)
        {
            std::string result = "(";
            for (size_t i = 0; i < a.ndim(); ++i)
            {
                if (i > 0) result += ", ";
                result += std::to_string(a.stride(i));
            }
            result += ")";
            return result;
        }

        inline std::string format_dtype(const nanobind::ndarray<>& a)
        {
            auto dtype = a.dtype();
            if (dtype == nanobind::dtype<uint8_t>()) return "uint8";
            if (dtype == nanobind::dtype<int8_t>()) return "int8";
            if (dtype == nanobind::dtype<uint16_t>()) return "uint16";
            if (dtype == nanobind::dtype<int16_t>()) return "int16";
            if (dtype == nanobind::dtype<int32_t>()) return "int32";
            if (dtype == nanobind::dtype<float>()) return "float32";
            if (dtype == nanobind::dtype<double>()) return "float64";
            return "unknown";
        }

        // Translated from cv2_numpy.cpp in OpenCV source code
        // A custom allocator for cv::Mat that attaches an owner to the cv::Mat
        class CvnpAllocator : public cv::MatAllocator
        {
        public:
            CvnpAllocator() = default;
            ~CvnpAllocator() = default;

            // Attaches an owner to a cv::Mat
            static void attach_nparray(cv::Mat &m, nanobind::handle owner)
            {
                static CvnpAllocator instance;

                // Ensure no existing custom allocator to avoid accidental double attachment
                if (m.u && m.allocator) {
                    throw std::logic_error("attach_nparray: cv::Mat already has a custom allocator attached");
                }

                cv::UMatData* u = new cv::UMatData(&instance);
                u->data = u->origdata = (uchar*)m.data;
                u->size = m.total();

                u->userdata = owner.inc_ref().ptr();
                u->refcount = 1;

#ifdef CVNP_NANO_DEBUG_ALLOCATOR
                ++nbAllocations;
                printf("CvnpAllocator::attach_nparray(py::array) nbAllocations=%d\n", nbAllocations);
#endif

                m.u = u;
                m.allocator = &instance;
            }

            cv::UMatData* allocate(int dims0, const int* sizes, int type, void* data, size_t* step, cv::AccessFlag flags, cv::UMatUsageFlags usageFlags) const override
            {
                throw nanobind::value_error("CvnpAllocator::allocate \"standard\" should never happen");
                // return stdAllocator->allocate(dims0, sizes, type, data, step, flags, usageFlags);
            }

            bool allocate(cv::UMatData* u, cv::AccessFlag accessFlags, cv::UMatUsageFlags usageFlags) const override
            {
                throw nanobind::value_error("CvnpAllocator::allocate \"copy\" should never happen");
                // return stdAllocator->allocate(u, accessFlags, usageFlags);
            }

            void deallocate(cv::UMatData* u) const override
            {
                if(!u)
                {
#ifdef CVNP_NANO_DEBUG_ALLOCATOR
                    printf("CvnpAllocator::deallocate() with null ptr!!! nbAllocations=%d\n", nbAllocations);
#endif
                    return;
                }

                // This function can be called from anywhere, so need the GIL
                nanobind::gil_scoped_acquire gil;
                assert(u->urefcount >= 0);
                assert(u->refcount >= 0);
                if(u->refcount == 0)
                {
                    PyObject* o = (PyObject*)u->userdata;
                    Py_XDECREF(o);
                    delete u;
#ifdef CVNP_NANO_DEBUG_ALLOCATOR
                    --nbAllocations;
                    printf("CvnpAllocator::deallocate() nbAllocations=%d\n", nbAllocations);
#endif
                }
                else
                {
#ifdef CVNP_NANO_DEBUG_ALLOCATOR
                    printf("CvnpAllocator::deallocate() - not doing anything since urefcount=%d nbAllocations=%d\n",
                            u->urefcount,
                           nbAllocations);
#endif
                }
            }
        };


        inline nanobind::dlpack::dtype determine_np_dtype(int cv_depth)
        {
            for (auto format_synonym : synonyms::get_type_synonyms())
                if (format_synonym.cv_depth == cv_depth)
                    return format_synonym.dtype;

            std::string msg = "numpy does not support this OpenCV depth: " + std::to_string(cv_depth) +  " (in determine_np_dtype)";
            throw std::invalid_argument(msg.c_str());
        }

        inline int determine_cv_depth(nanobind::dlpack::dtype dt)
        {
            for (auto format_synonym : synonyms::get_type_synonyms())
                if (format_synonym.dtype == dt)
                    return format_synonym.cv_depth;

            std::string msg = std::string("OpenCV does not support this numpy array type (in determine_np_dtype)!");
            throw std::invalid_argument(msg.c_str());
        }

        inline int determine_cv_type(const nanobind::ndarray<>& a, int depth)
        {
            if (a.ndim() < 2)
                throw std::invalid_argument("determine_cv_type needs at least two dimensions");
            
            // For 2D arrays, single channel
            if (a.ndim() == 2)
                return CV_MAKETYPE(depth, 1);
            // For 3D arrays, treat last dimension as channels (for RGB images, etc.)
            else if (a.ndim() == 3)
            {
                int nb_channels = static_cast<int>(a.shape(2));
                return CV_MAKETYPE(depth, nb_channels);
            }
            // For 4D+ arrays, single channel (true multi-dimensional)
            else
            {
                return CV_MAKETYPE(depth, 1);
            }
        }

        inline std::vector<std::size_t> determine_shape(const cv::Mat& m)
        {
            if (m.dims > 2) {
                std::vector<std::size_t> shape;
                for (int i = 0; i < m.dims; ++i)
                    shape.push_back(static_cast<size_t>(m.size[i]));

                if (m.channels() > 1)
                    shape.push_back(static_cast<size_t>(m.channels()));
                
                return shape;
            }
            else {
                if (m.channels() == 1) {
                    return {
                        static_cast<size_t>(m.rows),
                        static_cast<size_t>(m.cols)
                    };
                }
                return {
                    static_cast<size_t>(m.rows),
                    static_cast<size_t>(m.cols),
                    static_cast<size_t>(m.channels())
                };
            }
        }

        inline std::vector<int64_t> determine_strides(const cv::Mat& m) {
            if (m.dims > 2) {
                std::vector<int64_t> strides;
                for (int i = 0; i < m.dims; ++i)
                    strides.push_back(static_cast<int64_t>(m.step[i] / m.elemSize1()));

                if (m.channels() > 1)
                    strides.push_back(1);

                return strides;
            }
            else {
                // Return strides in nb element (not bytes)
                if (m.channels() == 1) {
                    return {
                        static_cast<int64_t>(m.step[0] / m.elemSize1()), // row stride
                        static_cast<int64_t>(m.step[1] / m.elemSize1())  // column stride
                    };
                }
                return {
                    static_cast<int64_t>(m.step[0] / m.elemSize1()), // row stride
                    static_cast<int64_t>(m.step[1] / m.elemSize1()), // column stride
                    static_cast<int64_t>(1) // channel stride
                };
            }
        }

        inline int determine_ndim(const cv::Mat& m)
        {
            if (m.dims > 2) {
                return m.channels() == 1 ? m.dims : m.dims + 1;
            }
            else {
                return m.channels() == 1 ? 2 : 3;
            }
        }
    } // namespace detail


    inline nanobind::ndarray<> mat_to_nparray(const cv::Mat &m, nanobind::handle owner)
    {
        void *data = static_cast<void *>(m.data);
        size_t ndim = detail::determine_ndim(m);

        // Test if m is contiguous
        if (!m.isContinuous())
        {
            throw std::invalid_argument("cvnp::mat_to_nparray / Only contiguous cv::Mat are supported. / Please use cv::Mat::clone() to convert your matrix");
        }

        std::vector<size_t> shape = detail::determine_shape(m);
        std::vector<int64_t> strides = detail::determine_strides(m);
        nanobind::dlpack::dtype dtype = detail::determine_np_dtype(m.depth());

        auto a = nanobind::ndarray<>(
            data,
            ndim,
            shape.data(),
            owner,
            strides.data(),
            dtype
        );
        return a;
    }


    inline bool is_array_contiguous(const nanobind::ndarray<>& a)
    {
        if (a.ndim() < 2)
        {
            std::string error_msg = 
                "cvnp_nano only supports arrays with at least 2 dimensions.\n"
                "Array info:\n"
                "  Shape: " + detail::format_shape(a) + "\n"
                "  Dtype: " + detail::format_dtype(a) + "\n"
                "Hint: Reshape your array to have at least 2 dimensions.\n"
                "  Example: arr.reshape((1, -1)) for row vector, arr.reshape((-1, 1)) for column vector";
            throw std::invalid_argument(error_msg);
        }

        if (a.ndim() == 2)
        {
            return a.stride(0) == a.shape(1) && a.stride(1) == 1;
        }
        else if (a.ndim() == 3)
        {
            return a.stride(0) == a.shape(1) * a.shape(2) && 
                   a.stride(1) == a.shape(2) && 
                   a.stride(2) == 1;
        }
        else
        {
            // For higher dimensions, check C-contiguous layout
            int64_t expected_stride = 1;
            for (int i = a.ndim() - 1; i >= 0; --i)
            {
                if (a.stride(i) != expected_stride)
                    return false;
                expected_stride *= a.shape(i);
            }
            return true;
        }
    }


    inline cv::Mat nparray_to_mat(nanobind::ndarray<>& a, nanobind::handle owner)
    {
        // note: empty arrays are not contiguous, but that's fine. Just
        //       make sure to not access mutable_data
        bool is_contiguous = is_array_contiguous(a);
        bool is_not_empty = a.size() != 0;
        if (! is_contiguous && is_not_empty) {
            std::string error_msg = 
                "cvnp_nano only supports contiguous numpy arrays.\n"
                "Array info:\n"
                "  Shape: " + detail::format_shape(a) + "\n"
                "  Strides: " + detail::format_strides(a) + "\n"
                "  Dtype: " + detail::format_dtype(a) + "\n"
                "Hint: Use np.ascontiguousarray() to convert your array:\n"
                "  contiguous_arr = np.ascontiguousarray(your_array)";
            throw std::invalid_argument(error_msg);
        }

        int depth = detail::determine_cv_depth(a.dtype());
        int type = detail::determine_cv_type(a, depth);
        
        cv::Mat m;
        
        // Use multi-dimensional constructor for all cases
        // For 2D/3D arrays: create 2D Mat (ndims=2) with channels encoded in type
        // For 4D+ arrays: create true multi-dimensional Mat
        if (a.ndim() <= 3)
        {
            // 2D or 3D (as 2D with channels): use first 2 dimensions
            int sizes[2] = {
                static_cast<int>(a.shape(0)),  // rows
                static_cast<int>(a.shape(1))   // cols
            };
            m = cv::Mat(2, sizes, type, is_not_empty ? a.data() : nullptr);
        }
        else
        {
            // True multi-dimensional (4D+)
            std::vector<int> sizes;
            for (size_t i = 0; i < a.ndim(); ++i)
                sizes.push_back(static_cast<int>(a.shape(i)));
            
            m = cv::Mat(static_cast<int>(sizes.size()), sizes.data(), type, is_not_empty ? a.data() : nullptr);
        }

        if (is_not_empty)
            detail::CvnpAllocator::attach_nparray(m, owner);

        return m;
    }

    inline void print_types_synonyms()
    {
        std::cout << synonyms::print_types_synonyms_str();
    }

} // namespace cvnp_nano

#ifdef __clang__
#pragma clang diagnostic pop
#elif defined(__GNUC__)
#pragma GCC diagnostic pop
#endif
