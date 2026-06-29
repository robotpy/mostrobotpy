from wpilib import NiDsPS5Controller
from wpilib.simulation import NiDsPS5ControllerSim
from driverstation.joystick_test_macros import button_test, axis_test


def test_buttons():
    def ps_5_button_test(btn_name):
        button_test(NiDsPS5Controller, NiDsPS5ControllerSim, btn_name)

    def ps_5_axis_test(axis_name):
        axis_test(NiDsPS5Controller, NiDsPS5ControllerSim, axis_name)

    ps_5_button_test("square_button")
    ps_5_button_test("cross_button")
    ps_5_button_test("circle_button")
    ps_5_button_test("triangle_button")

    ps_5_button_test("l_1_button")
    ps_5_button_test("r_1_button")
    ps_5_button_test("l_2_button")
    ps_5_button_test("r_2_button")

    ps_5_button_test("create_button")
    ps_5_button_test("options_button")

    ps_5_button_test("l_3_button")
    ps_5_button_test("r_3_button")

    ps_5_button_test("ps_button")
    ps_5_button_test("touchpad_button")

    ps_5_axis_test("left_x")
    ps_5_axis_test("right_x")
    ps_5_axis_test("left_y")
    ps_5_axis_test("right_y")
    ps_5_axis_test("l_2_axis")
    ps_5_axis_test("r_2_axis")
