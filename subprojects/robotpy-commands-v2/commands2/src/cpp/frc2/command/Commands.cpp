// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#include "frc2/command/Commands.h"

#include "frc2/command/ConditionalCommand.h"
#include "frc2/command/FunctionalCommand.h"
#include "frc2/command/InstantCommand.h"
#include "frc2/command/ParallelCommandGroup.h"
#include "frc2/command/ParallelDeadlineGroup.h"
#include "frc2/command/ParallelRaceGroup.h"
#include "frc2/command/PrintCommand.h"
#include "frc2/command/ProxyScheduleCommand.h"
#include "frc2/command/RepeatCommand.h"
#include "frc2/command/RunCommand.h"
#include "frc2/command/SequentialCommandGroup.h"
#include "frc2/command/WaitCommand.h"
#include "frc2/command/WaitUntilCommand.h"

using namespace frc2;

// Factories

std::shared_ptr<Command> cmd::None() {
  return std::make_shared<InstantCommand>();
}

std::shared_ptr<Command> cmd::RunOnce(std::function<void()> action,
                        std::initializer_list<std::shared_ptr<Subsystem>> requirements) {
  return std::make_shared<InstantCommand>(std::move(action), requirements);
}

std::shared_ptr<Command> cmd::RunOnce(std::function<void()> action,
                        std::span<std::shared_ptr<Subsystem>> requirements) {
  return std::make_shared<InstantCommand>(std::move(action), requirements);
}

std::shared_ptr<Command> cmd::Run(std::function<void()> action,
                    std::initializer_list<std::shared_ptr<Subsystem>> requirements) {
  return std::make_shared<RunCommand>(std::move(action), requirements);
}

std::shared_ptr<Command> cmd::Run(std::function<void()> action,
                    std::span<std::shared_ptr<Subsystem>> requirements) {
  return std::make_shared<RunCommand>(std::move(action), requirements);
}

std::shared_ptr<Command> cmd::StartEnd(std::function<void()> start, std::function<void()> end,
                         std::initializer_list<std::shared_ptr<Subsystem>> requirements) {
  return std::make_shared<FunctionalCommand>(
             std::move(start), [] {},
             [end = std::move(end)](bool interrupted) { end(); },
             [] { return false; }, requirements);
}

std::shared_ptr<Command> cmd::StartEnd(std::function<void()> start, std::function<void()> end,
                         std::span<std::shared_ptr<Subsystem>> requirements) {
  return std::make_shared<FunctionalCommand>(
             std::move(start), [] {},
             [end = std::move(end)](bool interrupted) { end(); },
             [] { return false; }, requirements);
}

std::shared_ptr<Command> cmd::RunEnd(std::function<void()> run, std::function<void()> end,
                       std::initializer_list<std::shared_ptr<Subsystem>> requirements) {
  return std::make_shared<FunctionalCommand>([] {}, std::move(run),
                           [end = std::move(end)](bool interrupted) { end(); },
                           [] { return false; }, requirements);
}

std::shared_ptr<Command> cmd::RunEnd(std::function<void()> run, std::function<void()> end,
                       std::span<std::shared_ptr<Subsystem>> requirements) {
  return std::make_shared<FunctionalCommand>([] {}, std::move(run),
                           [end = std::move(end)](bool interrupted) { end(); },
                           [] { return false; }, requirements);
}

std::shared_ptr<Command> cmd::Print(std::string_view msg) {
  return std::make_shared<PrintCommand>(msg);
}

std::shared_ptr<Command> cmd::Wait(units::second_t duration) {
  return std::make_shared<WaitCommand>(duration);
}

std::shared_ptr<Command> cmd::WaitUntil(std::function<bool()> condition) {
  return std::make_shared<WaitUntilCommand>(condition);
}

std::shared_ptr<Command> cmd::Either(std::shared_ptr<Command> onTrue, std::shared_ptr<Command> onFalse,
                       std::function<bool()> selector) {
  return std::make_shared<ConditionalCommand>(std::move(onTrue),
                            std::move(onFalse), std::move(selector));
}

std::shared_ptr<Command> cmd::Sequence(std::vector<std::shared_ptr<Command> >&& commands) {
  return std::make_shared<SequentialCommandGroup>(std::move(commands));
}

std::shared_ptr<Command> cmd::RepeatingSequence(std::vector<std::shared_ptr<Command> >&& commands) {
  return std::make_shared<RepeatCommand>(Sequence(std::move(commands)));
}

std::shared_ptr<Command> cmd::Parallel(std::vector<std::shared_ptr<Command> >&& commands) {
  return std::make_shared<ParallelCommandGroup>(std::move(commands));
}

std::shared_ptr<Command> cmd::Race(std::vector<std::shared_ptr<Command> >&& commands) {
  return std::make_shared<ParallelRaceGroup>(std::move(commands));
}

std::shared_ptr<Command> cmd::Deadline(std::shared_ptr<Command> deadline,
                         std::vector<std::shared_ptr<Command> >&& others) {
  return std::make_shared<ParallelDeadlineGroup>(std::move(deadline),
                               std::move(others));
}
