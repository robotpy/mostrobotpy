from wpiutil_test import module


def test_load_array_int():
    assert module.load_array_int((1, 2, 3, 4)) == (1, 2, 3, 4)
    assert module.load_array_int([1, 2, 3, 4]) == (1, 2, 3, 4)


def test_load_array_annotation():
    assert (
        module.load_array_int.__doc__
        == "load_array_int(arg: collections.abc.Sequence[int, int, int, int], /) -> tuple[int, int, int, int]"
    )
    assert (
        module.load_array_int1.__doc__
        == "load_array_int1(arg: collections.abc.Sequence[int], /) -> tuple[int]"
    )
