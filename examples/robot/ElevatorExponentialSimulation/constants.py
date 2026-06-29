#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

import math

import wpimath.units

K_MOTOR_PORT = 0
K_ENCODER_A_CHANNEL = 0
K_ENCODER_B_CHANNEL = 1
K_JOYSTICK_PORT = 0

K_ELEVATOR_KP = 0.75
K_ELEVATOR_KI = 0.0
K_ELEVATOR_KD = 0.0

K_ELEVATOR_MAX_V = 10.0  # volts (V)
K_ELEVATORK_S = 0.0  # volts (V)
K_ELEVATORK_G = 0.62  # volts (V)
K_ELEVATORK_V = 3.9  # volts (V)
K_ELEVATORK_A = 0.06  # volts (V)

K_ELEVATOR_GEARING = 5.0
K_ELEVATOR_DRUM_RADIUS = wpimath.units.inches_to_meters(1.0)
K_CARRIAGE_MASS = wpimath.units.lbs_to_kilograms(12)  # kg

K_SETPOINT = wpimath.units.inches_to_meters(42.875)
K_LOWERK_SETPOINT = wpimath.units.inches_to_meters(15)
# Encoder is reset to measure 0 at the bottom, so minimum height is 0.
K_MIN_ELEVATOR_HEIGHT = 0.0  # m
K_MAX_ELEVATOR_HEIGHT = wpimath.units.inches_to_meters(50)

# distance per pulse = (distance per revolution) / (pulses per revolution)
#  = (Pi * D) / ppr
K_ELEVATOR_ENCODER_DIST_PER_PULSE = 2.0 * math.pi * K_ELEVATOR_DRUM_RADIUS / 4096
