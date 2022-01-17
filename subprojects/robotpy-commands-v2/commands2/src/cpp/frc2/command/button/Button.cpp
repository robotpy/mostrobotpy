// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#include "frc2/command/button/Button.h"

using namespace frc2;

Button::Button(std::function<bool()> isPressed) : Trigger(isPressed) {}

Button Button::WhenPressed(std::shared_ptr<Command> command, bool interruptible) {
  WhenActive(command, interruptible);
  return *this;
}

// Button Button::WhenPressed(std::function<void()> toRun,
//                            std::initializer_list<std::shared_ptr<Subsystem>> requirements) {
//   WhenActive(std::move(toRun), requirements);
//   return *this;
// }

Button Button::WhenPressed(std::function<void()> toRun,
                           wpi::span<std::shared_ptr<Subsystem>> requirements) {
  WhenActive(std::move(toRun), requirements);
  return *this;
}

Button Button::WhileHeld(std::shared_ptr<Command> command, bool interruptible) {
  WhileActiveContinous(command, interruptible);
  return *this;
}

// Button Button::WhileHeld(std::function<void()> toRun,
//                          std::initializer_list<std::shared_ptr<Subsystem>> requirements) {
//   WhileActiveContinous(std::move(toRun), requirements);
//   return *this;
// }

Button Button::WhileHeld(std::function<void()> toRun,
                         wpi::span<std::shared_ptr<Subsystem>> requirements) {
  WhileActiveContinous(std::move(toRun), requirements);
  return *this;
}

Button Button::WhenHeld(std::shared_ptr<Command> command, bool interruptible) {
  WhileActiveOnce(command, interruptible);
  return *this;
}

Button Button::WhenReleased(std::shared_ptr<Command> command, bool interruptible) {
  WhenInactive(command, interruptible);
  return *this;
}

// Button Button::WhenReleased(std::function<void()> toRun,
//                             std::initializer_list<std::shared_ptr<Subsystem>> requirements) {
//   WhenInactive(std::move(toRun), requirements);
//   return *this;
// }

Button Button::WhenReleased(std::function<void()> toRun,
                            wpi::span<std::shared_ptr<Subsystem>> requirements) {
  WhenInactive(std::move(toRun), requirements);
  return *this;
}

Button Button::ToggleWhenPressed(std::shared_ptr<Command> command, bool interruptible) {
  ToggleWhenActive(command, interruptible);
  return *this;
}

Button Button::CancelWhenPressed(std::shared_ptr<Command> command) {
  CancelWhenActive(command);
  return *this;
}
