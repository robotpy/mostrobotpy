from typing import TypeVar

from wpimath.controller import ProfiledPIDController, ProfiledPIDControllerRadians

GenericProfiledPIDController = TypeVar(
    "GenericProfiledPIDController", ProfiledPIDControllerRadians, ProfiledPIDController
)
