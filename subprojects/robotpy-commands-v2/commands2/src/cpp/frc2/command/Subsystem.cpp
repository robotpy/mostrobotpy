// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#include "frc2/command/Subsystem.h"

#include "frc2/command/CommandPtr.h"

using namespace frc2;
Subsystem::~Subsystem() {
  CommandScheduler::GetInstance().UnregisterSubsystem(this);
}

void Subsystem::Periodic() {}

void Subsystem::SimulationPeriodic() {}

void Subsystem::SetDefaultCommand(std::shared_ptr<Command> defaultCommand) {
  CommandScheduler::GetInstance().SetDefaultCommand(this,
                                                    defaultCommand);
}

std::shared_ptr<Command> Subsystem::GetDefaultCommand() {
  return CommandScheduler::GetInstance().GetDefaultCommand(this);
}

std::shared_ptr<Command> Subsystem::GetCurrentCommand() {
  return CommandScheduler::GetInstance().Requiring(this);
}

void Subsystem::Register() {
  return CommandScheduler::GetInstance().RegisterSubsystem(this);
}
