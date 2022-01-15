from wpiutil_test import module


def test_span_load_int():
    assert module.load_span_int([1, 2, 3, 4]) == [1, 2, 3, 4]


def test_span_load_int():
    assert module.load_span_int([1, 2, 3]) == [1, 2, 3]


def test_span_load_bool():
    assert module.load_span_bool([True, False, True]) == [True, False, True]


def test_span_load_string():
    assert module.load_span_string(["a", "b", "c"]) == ["a", "b", "c"]


def test_span_load_stringview():
    assert module.load_span_string_view(["a", "b", "c"]) == ["a", "b", "c"]


def test_span_load_vector():
    assert module.load_span_vector([["a"], ["b"], ["c"]]) == [["a"], ["b"], ["c"]]


def test_span_cast():
    assert module.cast_span() == [1, 2, 3]
