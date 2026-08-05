from __future__ import annotations

from dataclasses import dataclass
import inspect
from typing import Any

from hal import RobotMode
from wpilib._wpilib import OpMode


@dataclass(frozen=True)
class OpModeMetadata:
    mode: RobotMode
    name: str
    group: str
    description: str
    text_color: Any | None
    background_color: Any | None


_decorated_opmodes: list[type[OpMode]] = []


def attach_metadata(
    cls: type[OpMode],
    *,
    mode: RobotMode,
    name: str = "",
    group: str = "",
    description: str = "",
    text_color: Any | None = None,
    background_color: Any | None = None,
) -> type[OpMode]:
    if not inspect.isclass(cls) or not issubclass(cls, OpMode):
        raise TypeError("opmode decorator must be applied to an OpMode subclass")
    if "_wpilib_opmode_metadata" in cls.__dict__:
        raise ValueError("multiple opmode decorators are not allowed")

    cls._wpilib_opmode_metadata = OpModeMetadata(
        mode, name or cls.__name__, group, description, text_color, background_color
    )
    _decorated_opmodes.append(cls)
    return cls


def decorated_opmodes() -> tuple[type[OpMode], ...]:
    return tuple(_decorated_opmodes)
