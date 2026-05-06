#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

from wpilib import Gamepad, PeriodicOpMode
from wpilib.opmoderobot import teleop


@teleop
class DefaultTeleMode(PeriodicOpMode):
    def __init__(self, robot):
        super().__init__()
        self.robot = robot
        self.gamepad = Gamepad(0)

    def periodic(self):
        self.robot.motor0.setThrottle(-self.gamepad.getLeftY())
        self.robot.motor1.setThrottle(-self.gamepad.getRightY())
        self.robot.motor2.setThrottle(-self.gamepad.getLeftX())
        self.robot.motor3.setThrottle(-self.gamepad.getRightX())
        self.robot.servo0.setPosition(self.gamepad.getLeftTriggerAxis())
        self.robot.servo1.setPosition(self.gamepad.getRightTriggerAxis())
