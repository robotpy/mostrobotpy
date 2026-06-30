import pytest
import wpimath_test


def test_units_attributes():
    assert wpimath_test.SomeClass.S_CONSTANT == 2
    assert wpimath_test.SomeClass.MS_CONSTANT_1 == 20  # the unit is ms, not seconds
    assert wpimath_test.SomeClass.MS_CONSTANT_2 == 0.050
    assert wpimath_test.SomeClass.MS_CONSTANT_3 == 200


def test_units_check_default_by_name_1():
    sc = wpimath_test.SomeClass()

    assert sc.check_default_by_name_1(0.020) == True
    assert sc.check_default_by_name_1() == True

    with pytest.raises(RuntimeError):
        sc.check_default_by_name_1(100)


def test_units_check_default_by_name_2():
    sc = wpimath_test.SomeClass()

    assert sc.check_default_by_name_2(0.050) == True
    assert sc.check_default_by_name_2() == True

    with pytest.raises(RuntimeError):
        sc.check_default_by_name_2(100)


def test_units_check_default_by_num_1():
    sc = wpimath_test.SomeClass()

    assert sc.check_default_by_num_1(0.050) == True
    assert sc.check_default_by_num_1() == True

    with pytest.raises(RuntimeError):
        sc.check_default_by_num_1(100)


def test_units_check_default_by_num_2():
    sc = wpimath_test.SomeClass()

    assert sc.check_default_by_num_2(0.050) == True
    assert sc.check_default_by_num_2() == True

    with pytest.raises(RuntimeError):
        sc.check_default_by_num_2(100)


def test_units_ft():
    assert wpimath_test.SomeClass.FIVE_FT == 5.0


def test_units_ft_2_m():
    sc = wpimath_test.SomeClass()

    assert sc.ft_2_m(3) == 0.9144


def test_units_ms_2_s():
    sc = wpimath_test.SomeClass()

    assert sc.ms_2_s(20) == 0.020


def test_units_s_2_ms():
    sc = wpimath_test.SomeClass()

    assert sc.s_2_ms(0.2) == 200.0
