// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#include "frc2/command/button/CommandJoystick.h"

using namespace frc2;

#define loop (loop_arg ? *loop_arg : CommandScheduler::GetInstance().GetDefaultButtonLoop())

Trigger CommandJoystick::Button(int button, std::optional<frc::EventLoop*> loop_arg) const {
  return GenericHID::Button(button, loop).CastTo<class Trigger>();
}

Trigger CommandJoystick::Trigger(std::optional<frc::EventLoop*> loop_arg) const {
  return Joystick::Trigger(loop).CastTo<class Trigger>();
}

Trigger CommandJoystick::Top(std::optional<frc::EventLoop*> loop_arg) const {
  return Joystick::Top(loop).CastTo<class Trigger>();
}
