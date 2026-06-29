#!/usr/bin/env python3
#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#


import wpilib


class MyRobot(wpilib.TimedRobot):
    """
    This is a sample program that uses mecanum drive with a gyro sensor to maintain rotation vectors
    in relation to the starting orientation of the robot (field-oriented controls).
    """

    K_FRONT_LEFT_CHANNEL = 0
    K_REAR_LEFT_CHANNEL = 1
    K_FRONT_RIGHT_CHANNEL = 2
    K_REAR_RIGHT_CHANNEL = 3
    K_IMU_MOUNT_ORIENTATION = wpilib.OnboardIMU.MountOrientation.FLAT
    K_JOYSTICK_PORT = 0

    def __init__(self) -> None:
        """Robot initialization function"""
        super().__init__()

        self.imu = wpilib.OnboardIMU(self.K_IMU_MOUNT_ORIENTATION)
        self.joystick = wpilib.Joystick(self.K_JOYSTICK_PORT)

        front_left = wpilib.PWMSparkMax(self.K_FRONT_LEFT_CHANNEL)
        rear_left = wpilib.PWMSparkMax(self.K_REAR_LEFT_CHANNEL)
        front_right = wpilib.PWMSparkMax(self.K_FRONT_RIGHT_CHANNEL)
        rear_right = wpilib.PWMSparkMax(self.K_REAR_RIGHT_CHANNEL)

        front_right.set_inverted(True)
        rear_right.set_inverted(True)

        self.robot_drive = wpilib.MecanumDrive(
            front_left, rear_left, front_right, rear_right
        )

    def teleop_periodic(self) -> None:
        self.robot_drive.drive_cartesian(
            -self.joystick.get_y(),
            -self.joystick.get_x(),
            -self.joystick.get_z(),
            self.imu.get_rotation_2_d(),
        )
