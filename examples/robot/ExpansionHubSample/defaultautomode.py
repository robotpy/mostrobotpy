#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

from wpilib import PeriodicOpMode, Timer
from wpilib.opmoderobot import autonomous


@autonomous
class DefaultAutoMode(PeriodicOpMode):
    def __init__(self, robot):
        super().__init__()
        self.robot = robot
        self.timer = Timer()

    def start(self):
        self.timer.reset()
        self.timer.start()

    def periodic(self):
        if self.timer.get() < 2.0:
            self.robot.motor0.setThrottle(0.5)
            self.robot.motor1.setThrottle(0.5)
        elif self.timer.get() < 4.0:
            self.robot.motor0.setThrottle(0.9)
            self.robot.motor1.setThrottle(0.9)
        else:
            self.robot.motor0.setThrottle(0.0)
            self.robot.motor1.setThrottle(0.0)
