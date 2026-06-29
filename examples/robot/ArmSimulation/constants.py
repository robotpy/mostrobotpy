#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

import math

from wpimath import units


class Constants:
    K_MOTOR_PORT = 0
    K_ENCODER_A_CHANNEL = 0
    K_ENCODER_B_CHANNEL = 1
    K_JOYSTICK_PORT = 0

    K_ARM_POSITION_KEY = "ArmPosition"
    K_ARM_P_KEY = "ArmP"

    # The P gain for the PID controller that drives this arm.
    K_DEFAULT_ARM_KP = 50.0
    K_DEFAULT_ARM_SETPOINT_DEGREES = 75.0

    # distance per pulse = (angle per revolution) / (pulses per revolution)
    #  = (2 * PI rads) / (4096 pulses)
    K_ARM_ENCODER_DIST_PER_PULSE = 2.0 * math.pi / 4096

    K_ARM_REDUCTION = 200
    K_ARM_MASS = 8.0  # Kilograms
    K_ARM_LENGTH = units.inches_to_meters(30)
    K_MIN_ANGLE_RADS = units.degrees_to_radians(-75)
    K_MAX_ANGLE_RADS = units.degrees_to_radians(255)
