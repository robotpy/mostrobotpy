
import wpiutil_test

def test_stringref_load():
    assert wpiutil_test.load_stringref("something") == "something"

def test_stringref_cast():
    assert wpiutil_test.cast_stringref() == "casted"
