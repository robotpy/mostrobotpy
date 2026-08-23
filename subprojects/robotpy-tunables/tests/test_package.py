from importlib.resources import files


def test_package_includes_py_typed_marker():
    assert files("tunables").joinpath("py.typed").is_file()
