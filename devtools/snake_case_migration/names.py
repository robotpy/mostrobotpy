from __future__ import annotations

from typing import Literal

from semiwrap.name_transform import resolve_name_transform

NameKind = Literal["function", "method", "attribute", "enum_value", "parameter"]

DEFAULT_ACRONYMS: tuple[str, ...] = (
    "mDNS",
    "DS",
    "CAN",
    "PWM",
    "I2C",
    "SPI",
    "NT",
    "JSON",
    "PID",
    "IMU",
    "HAL",
    "JNI",
    "USB",
    "HTTP",
    "URI",
    "URL",
    "CPU",
    "FPGA",
    "FMS",
    "PCM",
    "PDP",
    "PDH",
    "RIO",
    "OpMode",
)

_SNAKE_TRANSFORM = resolve_name_transform("snake_case", acronyms=DEFAULT_ACRONYMS)
_CAPS_TRANSFORM = resolve_name_transform("CAPS_CASE", acronyms=DEFAULT_ACRONYMS)


def is_dunder(name: str) -> bool:
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


def is_probably_type_name(name: str) -> bool:
    if not name or "_" in name or is_dunder(name):
        return False
    return name[0].isupper() and any(ch.islower() for ch in name[1:])


def to_snake_case(name: str, kind: NameKind = "method") -> str:
    if is_dunder(name):
        return name
    return _SNAKE_TRANSFORM(name, kind)


def to_caps_case(name: str) -> str:
    if is_dunder(name):
        return name
    return _CAPS_TRANSFORM(name, "enum_value")
