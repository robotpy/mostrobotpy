
#pragma once

#include "wpystruct.h"

/**
    Call a function to retrieve the (type string, schema) for each nested struct
*/
void for_each_nested(
    const py::type& t,
    const std::function<void(std::string_view, std::string_view)>& fn);

/**
    Retrieve the type name for the specified type
*/
py::str get_type_name(const py::type& t);

/**
    Retrieve schema for the specified type
*/
py::str get_schema(const py::type& t);

/**
    Returns the serialized size in bytes
*/
size_t get_size(const py::type& t);

/**
    Serialize object into byte buffer
*/
py::bytes pack(const WPyStruct& v);

/**
    Serialize objects into byte buffer
*/
py::bytes pack_array(const py::sequence& seq);

/**
    Serialize object into byte buffer. Buffer must be exact size.
*/
void pack_into(const WPyStruct& v, py::buffer& b);

/**
    Convert byte buffer into object of specified type. Buffer must be exact
    size.
*/
WPyStruct unpack(const py::type& t, const py::buffer& b);

/**
    Convert byte buffer into list of objects of specified type. Buffer must be
    exact size.
*/
py::typing::List<WPyStruct> unpack_array(const py::type& t, const py::buffer& b);

// /**
//     Convert byte buffer into passed in object. Buffer must be exact
//     size.
// */
// void unpack_into(const py::buffer &b, WPyStruct *v);
