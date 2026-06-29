#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

import math

import wpimath.units


class DriveConstants:
    K_LEFT_MOTOR_1_PORT = 0
    K_LEFT_MOTOR_2_PORT = 1
    K_RIGHT_MOTOR_1_PORT = 2
    K_RIGHT_MOTOR_2_PORT = 3

    K_LEFT_ENCODER_PORTS = (0, 1)
    K_RIGHT_ENCODER_PORTS = (2, 3)
    K_LEFT_ENCODER_REVERSED = False
    K_RIGHT_ENCODER_REVERSED = True

    K_ENCODER_CPR = 1024
    K_WHEEL_DIAMETER = wpimath.units.inches_to_meters(6)
    # Assumes the encoders are directly mounted on the wheel shafts
    K_ENCODER_DISTANCE_PER_PULSE = (K_WHEEL_DIAMETER * math.pi) / K_ENCODER_CPR


class ShooterConstants:
    K_ENCODER_PORTS = (4, 5)
    K_ENCODER_REVERSED = False
    K_ENCODER_CPR = 1024
    # Distance units will be rotations
    K_ENCODER_DISTANCE_PER_PULSE = 1.0 / K_ENCODER_CPR

    K_SHOOTER_MOTOR_PORT = 4
    K_FEEDER_MOTOR_PORT = 5

    K_SHOOTER_FREE_RPS = 5300.0
    K_SHOOTER_TARGET_RPS = 4000.0
    K_SHOOTER_TOLERANCE_RPS = 50.0

    # These are not real PID gains, and will have to be tuned for your specific robot.
    K_P = 1.0

    # On a real robot the feedforward constants should be empirically determined; these are
    # reasonable guesses.
    K_S = 0.05  # V
    # Should have value 12V at free velocity
    K_V = 12.0 / K_SHOOTER_FREE_RPS  # V/(rot/s)
    K_A = 0.0  # V/(rot/s^2)

    K_FEEDER_VELOCITY = 0.5


class IntakeConstants:
    K_MOTOR_PORT = 6
    K_SOLENOID_PORTS = (2, 3)


class StorageConstants:
    K_MOTOR_PORT = 7
    K_BALL_SENSOR_PORT = 6


class AutoConstants:
    K_TIMEOUT = 3
    K_DRIVE_DISTANCE = 2.0  # m
    K_DRIVE_VELOCITY = 0.5


class OIConstants:
    K_DRIVER_CONTROLLER_PORT = 0
