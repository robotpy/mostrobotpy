// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#include "frc2/command/button/CommandPS4Controller.h"

using namespace frc2;

#define loop (loop_arg ? *loop_arg : CommandScheduler::GetInstance().GetDefaultButtonLoop())

Trigger CommandPS4Controller::Button(int button, std::optional<frc::EventLoop*> loop_arg) const {
  return GenericHID::Button(button, loop).CastTo<Trigger>();
}

Trigger CommandPS4Controller::Square(std::optional<frc::EventLoop*> loop_arg) const {
  return PS4Controller::Square(loop).CastTo<Trigger>();
}

Trigger CommandPS4Controller::Cross(std::optional<frc::EventLoop*> loop_arg) const {
  return PS4Controller::Cross(loop).CastTo<Trigger>();
}

Trigger CommandPS4Controller::Circle(std::optional<frc::EventLoop*> loop_arg) const {
  return PS4Controller::Circle(loop).CastTo<Trigger>();
}

Trigger CommandPS4Controller::Triangle(std::optional<frc::EventLoop*> loop_arg) const {
  return PS4Controller::Triangle(loop).CastTo<Trigger>();
}

Trigger CommandPS4Controller::L1(std::optional<frc::EventLoop*> loop_arg) const {
  return PS4Controller::L1(loop).CastTo<Trigger>();
}

Trigger CommandPS4Controller::R1(std::optional<frc::EventLoop*> loop_arg) const {
  return PS4Controller::R1(loop).CastTo<Trigger>();
}

Trigger CommandPS4Controller::L2(std::optional<frc::EventLoop*> loop_arg) const {
  return PS4Controller::L2(loop).CastTo<Trigger>();
}

Trigger CommandPS4Controller::R2(std::optional<frc::EventLoop*> loop_arg) const {
  return PS4Controller::R2(loop).CastTo<Trigger>();
}

Trigger CommandPS4Controller::Options(std::optional<frc::EventLoop*> loop_arg) const {
  return PS4Controller::Options(loop).CastTo<Trigger>();
}

Trigger CommandPS4Controller::L3(std::optional<frc::EventLoop*> loop_arg) const {
  return PS4Controller::L3(loop).CastTo<Trigger>();
}

Trigger CommandPS4Controller::R3(std::optional<frc::EventLoop*> loop_arg) const {
  return PS4Controller::R3(loop).CastTo<Trigger>();
}

Trigger CommandPS4Controller::PS(std::optional<frc::EventLoop*> loop_arg) const {
  return PS4Controller::PS(loop).CastTo<Trigger>();
}

Trigger CommandPS4Controller::Touchpad(std::optional<frc::EventLoop*> loop_arg) const {
  return PS4Controller::Touchpad(loop).CastTo<Trigger>();
}
