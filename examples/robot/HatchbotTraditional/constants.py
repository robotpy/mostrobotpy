#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

#
# The constants module is a convenience place for teams to hold robot-wide
# numerical or boolean constants. Don't use this for any other purpose!
#

import math
import wpilib

# Motors
K_LEFT_MOTOR_1_PORT = 0
K_LEFT_MOTOR_2_PORT = 1
K_RIGHT_MOTOR_1_PORT = 2
K_RIGHT_MOTOR_2_PORT = 3

# Encoders
K_LEFT_ENCODER_PORTS = (0, 1)
K_RIGHT_ENCODER_PORTS = (2, 3)
K_LEFT_ENCODER_REVERSED = False
K_RIGHT_ENCODER_REVERSED = True

K_ENCODER_CPR = 1024
K_WHEEL_DIAMETER_INCHES = 6
# Assumes the encoders are directly mounted on the wheel shafts
K_ENCODER_DISTANCE_PER_PULSE = (K_WHEEL_DIAMETER_INCHES * math.pi) / K_ENCODER_CPR

# Hatch
K_HATCH_SOLENOID_MODULE_TYPE = wpilib.PneumaticsModuleType.CTRE_PCM
K_HATCH_SOLENOID_MODULE = 0
K_HATCH_SOLENOID_PORTS = (0, 1)

# Autonomous
K_AUTO_DRIVE_DISTANCE_INCHES = 60
K_AUTO_BACKUP_DISTANCE_INCHES = 20
K_AUTO_DRIVE_VELOCITY = 0.5

# Operator Interface
K_DRIVER_CONTROLLER_PORT = 0

# Physical parameters
K_DRIVE_TRAIN_MOTOR_COUNT = 2
K_TRACK_WIDTH = 0.381 * 2
K_GEARING_RATIO = 8
K_WHEEL_RADIUS = 0.0508

# kEncoderResolution = -
