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

K_ELEVATOR_KP = 5.0
K_ELEVATOR_KI = 0.0
K_ELEVATOR_KD = 0.0

K_ELEVATORK_S = 0.0  # volts (V)
K_ELEVATORK_G = 0.762  # volts (V)
K_ELEVATORK_V = 0.762  # volt per velocity (V/(m/s))
K_ELEVATORK_A = 0.0  # volt per acceleration (V/(m/s^2))

K_ELEVATOR_GEARING = 10.0
K_ELEVATOR_DRUM_RADIUS = wpimath.units.inches_to_meters(2.0)
K_CARRIAGE_MASS = 4.0  # kg

K_SETPOINT = 0.75  # m
# Encoder is reset to measure 0 at the bottom, so minimum height is 0.
K_MIN_ELEVATOR_HEIGHT = 0.0  # m
K_MAX_ELEVATOR_HEIGHT = 1.25  # m

# distance per pulse = (distance per revolution) / (pulses per revolution)
#  = (Pi * D) / ppr
K_ELEVATOR_ENCODER_DIST_PER_PULSE = 2.0 * math.pi * K_ELEVATOR_DRUM_RADIUS / 4096
