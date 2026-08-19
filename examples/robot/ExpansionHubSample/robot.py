#!/usr/bin/env python3
#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

from wpilib import ExpansionHubMotor, ExpansionHubServo
from wpilib.opmoderobot import OpModeRobot


class Robot(OpModeRobot):
    def __init__(self):
        super().__init__()
        self.motor0 = ExpansionHubMotor(0, 0)
        self.motor1 = ExpansionHubMotor(0, 1)
        self.motor2 = ExpansionHubMotor(0, 2)
        self.motor3 = ExpansionHubMotor(0, 3)
        self.servo0 = ExpansionHubServo(0, 0)
        self.servo1 = ExpansionHubServo(0, 1)
