// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#pragma once

#include <functional>
#include <initializer_list>
#include <span>
#include <string>
#include <utility>
#include <vector>

#include "frc2/command/CommandPtr.h"
#include "frc2/command/SelectCommand.h"

namespace frc2 {
class Subsystem;

/**
 * Namespace for command factories.
 */
namespace cmd {

/**
 * Constructs a command that does nothing, finishing immediately.
 */
[[nodiscard]] std::shared_ptr<Command> None();

// Action Commands

/**
 * Constructs a command that runs an action once and finishes.
 *
 * @param action the action to run
 * @param requirements subsystems the action requires
 */
[[nodiscard]] std::shared_ptr<Command> RunOnce(
    std::function<void()> action,
    std::initializer_list<std::shared_ptr<Subsystem>> requirements);

/**
 * Constructs a command that runs an action once and finishes.
 *
 * @param action the action to run
 * @param requirements subsystems the action requires
 */
[[nodiscard]] std::shared_ptr<Command> RunOnce(std::function<void()> action,
                                 std::span<std::shared_ptr<Subsystem>> requirements = {});

/**
 * Constructs a command that runs an action every iteration until interrupted.
 *
 * @param action the action to run
 * @param requirements subsystems the action requires
 */
[[nodiscard]] std::shared_ptr<Command> Run(std::function<void()> action,
                             std::initializer_list<std::shared_ptr<Subsystem>> requirements);

/**
 * Constructs a command that runs an action every iteration until interrupted.
 *
 * @param action the action to run
 * @param requirements subsystems the action requires
 */
[[nodiscard]] std::shared_ptr<Command> Run(std::function<void()> action,
                             std::span<std::shared_ptr<Subsystem>> requirements = {});

/**
 * Constructs a command that runs an action once and another action when the
 * command is interrupted.
 *
 * @param start the action to run on start
 * @param end the action to run on interrupt
 * @param requirements subsystems the action requires
 */
[[nodiscard]] std::shared_ptr<Command> StartEnd(
    std::function<void()> start, std::function<void()> end,
    std::initializer_list<std::shared_ptr<Subsystem>> requirements);

/**
 * Constructs a command that runs an action once and another action when the
 * command is interrupted.
 *
 * @param start the action to run on start
 * @param end the action to run on interrupt
 * @param requirements subsystems the action requires
 */
[[nodiscard]] std::shared_ptr<Command> StartEnd(
    std::function<void()> start, std::function<void()> end,
    std::span<std::shared_ptr<Subsystem>> requirements = {});

/**
 * Constructs a command that runs an action every iteration until interrupted,
 * and then runs a second action.
 *
 * @param run the action to run every iteration
 * @param end the action to run on interrupt
 * @param requirements subsystems the action requires
 */
[[nodiscard]] std::shared_ptr<Command> RunEnd(std::function<void()> run,
                                std::function<void()> end,
                                std::initializer_list<std::shared_ptr<Subsystem>> requirements);

/**
 * Constructs a command that runs an action every iteration until interrupted,
 * and then runs a second action.
 *
 * @param run the action to run every iteration
 * @param end the action to run on interrupt
 * @param requirements subsystems the action requires
 */
[[nodiscard]] std::shared_ptr<Command> RunEnd(std::function<void()> run,
                                std::function<void()> end,
                                std::span<std::shared_ptr<Subsystem>> requirements = {});

/**
 * Constructs a command that prints a message and finishes.
 *
 * @param msg the message to print
 */
[[nodiscard]] std::shared_ptr<Command> Print(std::string_view msg);

// Idling Commands

/**
 * Constructs a command that does nothing, finishing after a specified duration.
 *
 * @param duration after how long the command finishes
 */
[[nodiscard]] std::shared_ptr<Command> Wait(units::second_t duration);

/**
 * Constructs a command that does nothing, finishing once a condition becomes
 * true.
 *
 * @param condition the condition
 */
[[nodiscard]] std::shared_ptr<Command> WaitUntil(std::function<bool()> condition);

// Selector Commands

/**
 * Runs one of two commands, based on the boolean selector function.
 *
 * @param onTrue the command to run if the selector function returns true
 * @param onFalse the command to run if the selector function returns false
 * @param selector the selector function
 */
[[nodiscard]] std::shared_ptr<Command> Either(std::shared_ptr<Command> onTrue, std::shared_ptr<Command> onFalse,
                                std::function<bool()> selector);

/**
 * Runs one of several commands, based on the selector function.
 *
 * @param selector the selector function
 * @param commands map of commands to select from
 */
template <typename Key>
[[nodiscard]] std::shared_ptr<Command> Select(
    std::function<Key()> selector,
    std::vector<std::pair<Key, std::shared_ptr<Command>>> commands) {
  return std::make_shared<SelectCommand<Key>>(std::move(selector), std::move(commands));
}

// Command Groups

namespace impl {

/**
 * Create a vector of commands.
 */
/*
template <typename... Args>
std::vector<CommandPtr> MakeVector(Args&&... args) {
  std::vector<CommandPtr> data;
  data.reserve(sizeof...(Args));
  (data.emplace_back(std::forward<Args>(args)), ...);
  return data;
}
*/

}  // namespace impl

/**
 * Runs a group of commands in series, one after the other.
 */
[[nodiscard]] std::shared_ptr<Command> Sequence(std::vector<std::shared_ptr<Command>>&& commands);

/**
 * Runs a group of commands in series, one after the other.
 */
/*
template <typename... Args>
[[nodiscard]] CommandPtr Sequence(Args&&... commands) {
  return Sequence(impl::MakeVector(std::forward<Args>(commands)...));
}
*/

/**
 * Runs a group of commands in series, one after the other. Once the last
 * command ends, the group is restarted.
 */
[[nodiscard]] std::shared_ptr<Command> RepeatingSequence(std::vector<std::shared_ptr<Command>>&& commands);

/**
 * Runs a group of commands in series, one after the other. Once the last
 * command ends, the group is restarted.
 */
/*
template <typename... Args>
[[nodiscard]] CommandPtr RepeatingSequence(Args&&... commands) {
  return RepeatingSequence(impl::MakeVector(std::forward<Args>(commands)...));
}
*/

/**
 * Runs a group of commands at the same time. Ends once all commands in the
 * group finish.
 */
[[nodiscard]] std::shared_ptr<Command> Parallel(std::vector<std::shared_ptr<Command>>&& commands);

/**
 * Runs a group of commands at the same time. Ends once all commands in the
 * group finish.
 */
/*
template <typename... Args>
[[nodiscard]] CommandPtr Parallel(Args&&... commands) {
  return Parallel(impl::MakeVector(std::forward<Args>(commands)...));
}
*/

/**
 * Runs a group of commands at the same time. Ends once any command in the group
 * finishes, and cancels the others.
 */
[[nodiscard]] std::shared_ptr<Command> Race(std::vector<std::shared_ptr<Command>>&& commands);

/**
 * Runs a group of commands at the same time. Ends once any command in the group
 * finishes, and cancels the others.
 */
/*
template <typename... Args>
[[nodiscard]] CommandPtr Race(Args&&... commands) {
  return Race(impl::MakeVector(std::forward<Args>(commands)...));
}
*/

/**
 * Runs a group of commands at the same time. Ends once a specific command
 * finishes, and cancels the others.
 */
[[nodiscard]] std::shared_ptr<Command> Deadline(std::shared_ptr<Command> deadline,
                                  std::vector<std::shared_ptr<Command>>&& others);

/**
 * Runs a group of commands at the same time. Ends once a specific command
 * finishes, and cancels the others.
 */
/*
template <typename... Args>
[[nodiscard]] CommandPtr Deadline(CommandPtr&& deadline, Args&&... commands) {
  return Deadline(std::move(deadline),
                  impl::MakeVector(std::forward<Args>(commands)...));
}
*/

}  // namespace cmd

}  // namespace frc2
