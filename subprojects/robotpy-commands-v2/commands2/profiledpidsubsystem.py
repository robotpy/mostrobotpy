# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.

from typing import Union, cast

from wpimath.trajectory import TrapezoidProfile

from .subsystem import Subsystem


class ProfiledPIDSubsystem(Subsystem):
    """
    A subsystem that uses a :class:`wpimath.controller.ProfiledPIDController`
    or :class:`wpimath.controller.ProfiledPIDControllerRadians` to
    control an output. The controller is run synchronously from the subsystem's
    :meth:`.periodic` method.
    """

    def __init__(
        self,
        controller,
        initial_position: float = 0,
    ):
        """Creates a new PIDSubsystem."""
        super().__init__()
        self._controller = controller
        self._enabled = False
        self.setGoal(initial_position)

    def periodic(self):
        """Updates the output of the controller."""
        if self._enabled:
            self.useOutput(
                self._controller.calculate(self.getMeasurement()),
                self._controller.getSetpoint(),
            )

    def getController(
        self,
    ):
        """Returns the controller"""
        return self._controller

    def setGoal(self, goal):
        """
        Sets the goal state for the subsystem.
        """
        self._controller.setGoal(goal)

    def useOutput(self, output: float, setpoint: TrapezoidProfile.State):
        """
        Uses the output from the controller object.
        """
        raise NotImplementedError(f"{self.__class__} must implement useOutput")

    def getMeasurement(self) -> float:
        """
        Returns the measurement of the process variable used by the
        controller object.
        """
        raise NotImplementedError(f"{self.__class__} must implement getMeasurement")

    def enable(self):
        """Enables the PID control. Resets the controller."""
        self._enabled = True
        self._controller.reset(self.getMeasurement())

    def disable(self):
        """Disables the PID control. Sets output to zero."""
        self._enabled = False
        self.useOutput(0, TrapezoidProfile.State())

    def isEnabled(self) -> bool:
        """
        Returns whether the controller is enabled.
        """
        return self._enabled
