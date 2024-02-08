from typing import Protocol, TypeVar

from wpimath.controller import ProfiledPIDController, ProfiledPIDControllerRadians
from wpimath.trajectory import TrapezoidProfile, TrapezoidProfileRadians

TProfiledPIDController = TypeVar(
    "TProfiledPIDController", ProfiledPIDControllerRadians, ProfiledPIDController
)
TTrapezoidProfileState = TypeVar(
    "TTrapezoidProfileState",
    TrapezoidProfileRadians.State,
    TrapezoidProfile.State,
)


class UseOutputFunction(Protocol):

    def __init__(self): ...

    def __call__(self, t: float, u: TTrapezoidProfileState) -> None: ...

    def accept(self, t: float, u: TTrapezoidProfileState) -> None: ...
