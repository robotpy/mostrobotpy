#
# These tests are leftover from the original pynetworktables tests
#

import pytest


@pytest.fixture(scope="function")
def table_1(nt):
    return nt.get_table("/test1")


@pytest.fixture(scope="function")
def table_2(nt):
    return nt.get_table("/test2")


def test_put_double(table_1):
    table_1.put_number("double", 42.42)
    assert table_1.get_number("double", None) == 42.42

    assert table_1.get_number("Non-Existent", 44.44) == 44.44


def test_put_boolean(table_1):
    table_1.put_boolean("boolean", True)
    assert table_1.get_boolean("boolean", None) == True

    assert table_1.get_boolean("Non-Existent", False) == False


def test_put_string(table_1):
    table_1.put_string("String", "Test 1")
    assert table_1.get_string("String", None) == "Test 1"

    assert table_1.get_string("Non-Existent", "Test 3") == "Test 3"


def test_getvalue_overloads(table_1):
    table_1.put_value("float", 35.5)
    assert table_1.get_value("float", None) == pytest.approx(35.5)

    table_1.put_value("integer", 950)
    assert table_1.get_value("integer", None) == pytest.approx(950)

    table_1.put_value("boolean", True)
    assert table_1.get_value("boolean", None) is True


def test_multi_data_type(table_1):
    table_1.put_number("double1", 1)
    table_1.put_number("double2", 2)
    table_1.put_number("double3", 3)
    table_1.put_boolean("bool1", False)
    table_1.put_boolean("bool2", True)
    table_1.put_string("string1", "String 1")
    table_1.put_string("string2", "String 2")
    table_1.put_string("string3", "String 3")

    assert table_1.get_number("double1", None) == 1
    assert table_1.get_number("double2", None) == 2
    assert table_1.get_number("double3", None) == 3
    assert table_1.get_boolean("bool1", None) == False
    assert table_1.get_boolean("bool2", None) == True
    assert table_1.get_string("string1", None) == "String 1"
    assert table_1.get_string("string2", None) == "String 2"
    assert table_1.get_string("string3", None) == "String 3"

    table_1.put_number("double1", 4)
    table_1.put_number("double2", 5)
    table_1.put_number("double3", 6)
    table_1.put_boolean("bool1", True)
    table_1.put_boolean("bool2", False)
    table_1.put_string("string1", "String 4")
    table_1.put_string("string2", "String 5")
    table_1.put_string("string3", "String 6")

    assert table_1.get_number("double1", None) == 4
    assert table_1.get_number("double2", None) == 5
    assert table_1.get_number("double3", None) == 6
    assert table_1.get_boolean("bool1", None) == True
    assert table_1.get_boolean("bool2", None) == False
    assert table_1.get_string("string1", None) == "String 4"
    assert table_1.get_string("string2", None) == "String 5"
    assert table_1.get_string("string3", None) == "String 6"


def test_multi_table(table_1, table_2):
    table_1.put_number("table1double", 1)
    table_1.put_boolean("table1boolean", True)
    table_1.put_string("table1string", "Table 1")

    assert table_2.get_number("table1double", None) == None
    assert table_2.get_boolean("table1boolean", None) == None
    assert table_2.get_string("table1string", None) == None

    table_2.put_number("table2double", 2)
    table_2.put_boolean("table2boolean", False)
    table_2.put_string("table2string", "Table 2")

    assert table_1.get_number("table2double", None) == None
    assert table_1.get_boolean("table2boolean", None) == None
    assert table_1.get_string("table2string", None) == None


# def test_get_table(nt, table1, table2):
#     assert nt.getTable("test1") is table1
#     assert nt.getTable("test2") is table2

#     assert nt.getTable("/test1") is table1
#     assert nt.getTable("/test2") is table2

#     assert nt.getTable("/test1/") is table1
#     assert nt.getTable("/test1/").path == "/test1"

#     assert table1 is not table2

#     table3 = nt.getTable("/test3")
#     assert table1 is not table3
#     assert table2 is not table3


# def test_get_subtable(nt, table1):
#     assert not table1.containsSubTable("test1")

#     st1 = table1.getSubTable("test1")

#     assert nt.getTable("/test1/test1") is st1
#     assert table1.getSubTable("test1") is st1

#     # weird, but true -- subtable only exists when key exists
#     assert not table1.containsSubTable("test1")
#     st1.putBoolean("hi", True)
#     assert table1.containsSubTable("test1")

#     assert table1.getSubTables() == ["test1"]
#     assert st1.getSubTables() == []


def test_getkeys(table_1):
    assert table_1.get_keys() == []
    assert not table_1.contains_key("hi")
    assert "hi" not in table_1

    table_1.put_boolean("hi", True)
    assert table_1.get_keys() == ["hi"]

    assert table_1.contains_key("hi")
    assert "hi" in table_1


def test_flags(table_1):
    table_1.put_boolean("foo", True)
    assert not table_1.is_persistent("foo")

    table_1.set_persistent("foo")
    assert table_1.is_persistent("foo")

    table_1.clear_persistent("foo")
    assert not table_1.is_persistent("foo")


# def test_delete(table1):
#     table1.putBoolean("foo", True)
#     assert table1.getBoolean("foo", None) == True

#     table1.delete("foo")
#     assert table1.getBoolean("foo", None) == None


def test_different_type(table_1):
    assert table_1.put_boolean("foo", True)
    assert table_1.get_boolean("foo", None) == True

    assert not table_1.put_number("foo", 1)
    assert table_1.get_boolean("foo", None) == True
