import ast
import pathlib

import commands2.button as button
import wpilib


WRAPPER_ROOT = pathlib.Path(__file__).parents[1] / "commands2" / "button"


def _wpilib_controller_class(name: str):
    return getattr(wpilib, name, None)


def test_controller_enum_references_match_generated_wpilib_names():
    failures: list[str] = []

    for path in sorted(WRAPPER_ROOT.glob("command*controller.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute):
                continue
            enum_attr = node.value
            if not isinstance(enum_attr, ast.Attribute):
                continue
            controller_name = enum_attr.attr
            if enum_attr.attr not in {"Button", "Axis"}:
                continue
            controller_attr = enum_attr.value
            if not isinstance(controller_attr, ast.Name):
                continue

            controller_cls = _wpilib_controller_class(controller_attr.id)
            if controller_cls is None:
                continue

            enum_cls = getattr(controller_cls, controller_name, None)
            if enum_cls is None:
                continue

            if not hasattr(enum_cls, node.attr):
                failures.append(
                    f"{path.name}:{node.lineno} {controller_attr.id}.{controller_name}.{node.attr}"
                )

    assert failures == []


def test_controller_helpers_are_snake_case_only():
    old_l_trigger = "L" + "Trigger"
    old_r_trigger = "R" + "Trigger"
    old_c_left = "C" + "Left"
    old_c_up = "C" + "Up"
    old_c_down = "C" + "Down"
    old_c_right = "C" + "Right"

    assert hasattr(button.CommandGameCubeController, "l_trigger")
    assert hasattr(button.CommandGameCubeController, "r_trigger")
    assert not hasattr(button.CommandGameCubeController, old_l_trigger)
    assert not hasattr(button.CommandGameCubeController, old_r_trigger)

    assert hasattr(button.CommandSwitch2GCController, "l_trigger")
    assert hasattr(button.CommandSwitch2GCController, "r_trigger")
    assert not hasattr(button.CommandSwitch2GCController, old_l_trigger)
    assert not hasattr(button.CommandSwitch2GCController, old_r_trigger)

    assert hasattr(button.CommandSwitchN64Controller, "c_left")
    assert hasattr(button.CommandSwitchN64Controller, "c_up")
    assert hasattr(button.CommandSwitchN64Controller, "c_down")
    assert hasattr(button.CommandSwitchN64Controller, "c_right")
    assert not hasattr(button.CommandSwitchN64Controller, old_c_left)
    assert not hasattr(button.CommandSwitchN64Controller, old_c_up)
    assert not hasattr(button.CommandSwitchN64Controller, old_c_down)
    assert not hasattr(button.CommandSwitchN64Controller, old_c_right)
