// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#include "frc2/command/button/Button.h"

using namespace frc2;

Button::Button(std::function<bool()> isPressed) : Trigger(isPressed) {}

Button Button::WhenPressed(std::shared_ptr<Command> command) {
  WPI_IGNORE_DEPRECATED
  WhenActive(command);
  WPI_UNIGNORE_DEPRECATED
  return *this;
}

/*
Button Button::WhenPressed(std::function<void()> toRun,
                           std::initializer_list<std::shared_ptr<Subsystem>> requirements) {
  WPI_IGNORE_DEPRECATED
  WhenActive(std::move(toRun), requirements);
  WPI_UNIGNORE_DEPRECATED
  return *this;
}
*/

Button Button::WhenPressed(std::function<void()> toRun,
                           std::span<std::shared_ptr<Subsystem>> requirements) {
  WPI_IGNORE_DEPRECATED
  WhenActive(std::move(toRun), requirements);
  WPI_UNIGNORE_DEPRECATED
  return *this;
}

Button Button::WhileHeld(std::shared_ptr<Command> command) {
  WPI_IGNORE_DEPRECATED
  WhileActiveContinous(command);
  WPI_UNIGNORE_DEPRECATED
  return *this;
}

/*
Button Button::WhileHeld(std::function<void()> toRun,
                         std::initializer_list<std::shared_ptr<Subsystem>> requirements) {
  WPI_IGNORE_DEPRECATED
  WhileActiveContinous(std::move(toRun), requirements);
  WPI_UNIGNORE_DEPRECATED
  return *this;
}
*/

Button Button::WhileHeld(std::function<void()> toRun,
                         std::span<std::shared_ptr<Subsystem>> requirements) {
  WPI_IGNORE_DEPRECATED
  WhileActiveContinous(std::move(toRun), requirements);
  WPI_UNIGNORE_DEPRECATED
  return *this;
}

Button Button::WhenHeld(std::shared_ptr<Command> command) {
  WPI_IGNORE_DEPRECATED
  WhileActiveOnce(command);
  WPI_UNIGNORE_DEPRECATED
  return *this;
}

Button Button::WhenReleased(std::shared_ptr<Command> command) {
  WPI_IGNORE_DEPRECATED
  WhenInactive(command);
  WPI_UNIGNORE_DEPRECATED
  return *this;
}

/*
Button Button::WhenReleased(std::function<void()> toRun,
                            std::initializer_list<std::shared_ptr<Subsystem>> requirements) {
  WPI_IGNORE_DEPRECATED
  WhenInactive(std::move(toRun), requirements);
  WPI_UNIGNORE_DEPRECATED
  return *this;
}
*/

Button Button::WhenReleased(std::function<void()> toRun,
                            std::span<std::shared_ptr<Subsystem>> requirements) {
  WPI_IGNORE_DEPRECATED
  WhenInactive(std::move(toRun), requirements);
  WPI_UNIGNORE_DEPRECATED
  return *this;
}

Button Button::ToggleWhenPressed(std::shared_ptr<Command> command) {
  WPI_IGNORE_DEPRECATED
  ToggleWhenActive(command);
  WPI_UNIGNORE_DEPRECATED
  return *this;
}

Button Button::CancelWhenPressed(std::shared_ptr<Command> command) {
  WPI_IGNORE_DEPRECATED
  CancelWhenActive(command);
  WPI_UNIGNORE_DEPRECATED
  return *this;
}
