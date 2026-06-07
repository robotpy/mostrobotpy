#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

from wpilib import DefaultUserControls, PeriodicOpMode
from wpilib.opmoderobot import teleop


@teleop
class DefaultTeleMode(PeriodicOpMode):
    def __init__(self, robot, user_controls: DefaultUserControls):
        super().__init__()
        self.robot = robot
        self.user_controls = user_controls

    def periodic(self):
        gamepad = self.user_controls.getGamepad(0)
        self.robot.motor0.setThrottle(-gamepad.getLeftY())
        self.robot.motor1.setThrottle(-gamepad.getRightY())
        self.robot.motor2.setThrottle(-gamepad.getLeftX())
        self.robot.motor3.setThrottle(-gamepad.getRightX())
        self.robot.servo0.setPosition(gamepad.getLeftTriggerAxis())
        self.robot.servo1.setPosition(gamepad.getRightTriggerAxis())
