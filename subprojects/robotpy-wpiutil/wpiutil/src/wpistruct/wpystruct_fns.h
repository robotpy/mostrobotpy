
#pragma once

#include "wpystruct.h"

/**
    Call a function to retrieve the (type string, schema) for each nested struct
*/
void forEachNested(
    const nb::type_object &t,
    const std::function<void(std::string_view, std::string_view)> &fn);

/**
    Retrieve the type name for the specified type
*/
nb::str getTypeName(const nb::type_object &t);

/**
    Retrieve schema for the specified type
*/
nb::str getSchema(const nb::type_object &t);

/**
    Returns the serialized size in bytes
*/
size_t getSize(const nb::type_object &t);

/**
    Serialize object into byte buffer
*/
nb::bytes pack(const WPyStruct &v);

/**
    Serialize objects into byte buffer
*/
nb::bytes packArray(const nb::sequence &seq);

/**
    Serialize object into byte buffer. Buffer must be exact size.
*/
void packInto(const WPyStruct &v, const nb::ndarray<uint8_t, nb::shape<-1>, nb::c_contig> &b);

/**
    Convert byte buffer into object of specified type. Buffer must be exact
    size.
*/
WPyStruct unpack(const nb::type_object &t, const nb::ndarray<const uint8_t, nb::shape<-1>, nb::c_contig> &b);

/**
    Convert byte buffer into list of objects of specified type. Buffer must be
    exact size.
*/
nb::typed<nb::list, WPyStruct> unpackArray(const nb::type_object &t, const nb::ndarray<const uint8_t, nb::shape<-1>, nb::c_contig> &b);

// /**
//     Convert byte buffer into passed in object. Buffer must be exact
//     size.
// */
// void unpackInto(const nb::buffer &b, WPyStruct *v);
