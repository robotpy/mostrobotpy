// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#include "frc2/command/button/CommandXboxController.h"

using namespace frc2;

#define loop (loop_arg ? *loop_arg : CommandScheduler::GetInstance().GetDefaultButtonLoop())

Trigger CommandXboxController::Button(int button, std::optional<frc::EventLoop*> loop_arg) const {
  return GenericHID::Button(button, loop).CastTo<Trigger>();
}

Trigger CommandXboxController::LeftBumper(std::optional<frc::EventLoop*> loop_arg) const {
  return XboxController::LeftBumper(loop).CastTo<Trigger>();
}

Trigger CommandXboxController::RightBumper(std::optional<frc::EventLoop*> loop_arg) const {
  return XboxController::RightBumper(loop).CastTo<Trigger>();
}

Trigger CommandXboxController::LeftStick(std::optional<frc::EventLoop*> loop_arg) const {
  return XboxController::LeftStick(loop).CastTo<Trigger>();
}

Trigger CommandXboxController::RightStick(std::optional<frc::EventLoop*> loop_arg) const {
  return XboxController::RightStick(loop).CastTo<Trigger>();
}

Trigger CommandXboxController::A(std::optional<frc::EventLoop*> loop_arg) const {
  return XboxController::A(loop).CastTo<Trigger>();
}

Trigger CommandXboxController::B(std::optional<frc::EventLoop*> loop_arg) const {
  return XboxController::B(loop).CastTo<Trigger>();
}

Trigger CommandXboxController::X(std::optional<frc::EventLoop*> loop_arg) const {
  return XboxController::X(loop).CastTo<Trigger>();
}

Trigger CommandXboxController::Y(std::optional<frc::EventLoop*> loop_arg) const {
  return XboxController::Y(loop).CastTo<Trigger>();
}

Trigger CommandXboxController::Back(std::optional<frc::EventLoop*> loop_arg) const {
  return XboxController::Back(loop).CastTo<Trigger>();
}

Trigger CommandXboxController::Start(std::optional<frc::EventLoop*> loop_arg) const {
  return XboxController::Start(loop).CastTo<Trigger>();
}

Trigger CommandXboxController::LeftTrigger(double threshold,
                                           std::optional<frc::EventLoop*> loop_arg) const {
  return XboxController::LeftTrigger(threshold, loop).CastTo<Trigger>();
}

Trigger CommandXboxController::RightTrigger(double threshold,
                                            std::optional<frc::EventLoop*> loop_arg) const {
  return XboxController::RightTrigger(threshold, loop).CastTo<Trigger>();
}
