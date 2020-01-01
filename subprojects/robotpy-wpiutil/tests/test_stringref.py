
from wpiutil_test import module

def test_stringref_load():
    assert module.load_stringref("something") == "something"

def test_stringref_cast():
    assert module.cast_stringref() == "casted"
