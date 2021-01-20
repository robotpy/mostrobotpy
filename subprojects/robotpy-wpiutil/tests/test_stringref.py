from wpiutil_test import module


def test_stringref_load():
    assert module.load_stringref("something") == "something"


def test_stringref_cast():
    assert module.cast_stringref() == "casted"


def test_array_load_int():
    assert module.load_array_int([1, 2, 3, 4]) == (1, 2, 3, 4)


def test_arrayref_load_int():
    assert module.load_arrayref_int([1, 2, 3]) == [1, 2, 3]


def test_arrayref_load_bool():
    assert module.load_arrayref_bool([True, False, True]) == [True, False, True]


def test_arrayref_load_string():
    assert module.load_arrayref_string(["a", "b", "c"]) == ["a", "b", "c"]


def test_arrayref_load_vector():
    assert module.load_arrayref_vector([["a"], ["b"], ["c"]]) == [["a"], ["b"], ["c"]]
