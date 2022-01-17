// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#pragma once

#ifdef _WIN32
#pragma warning(push)
#pragma warning(disable : 4521)
#endif

#include <limits>
#include <memory>
#include <type_traits>
#include <utility>
#include <vector>

#include <wpi/span.h>

#include "frc2/command/CommandGroupBase.h"
#include "frc2/command/CommandHelper.h"

namespace frc2 {

const size_t invalid_index = std::numeric_limits<size_t>::max();

/**
 * A CommandGroups that runs a list of commands in sequence.
 *
 * <p>As a rule, CommandGroups require the union of the requirements of their
 * component commands.
 */
class SequentialCommandGroup
    : public CommandGroupBase {
 public:
  /**
   * Creates a new SequentialCommandGroup.  The given commands will be run
   * sequentially, with the CommandGroup finishing when the last command
   * finishes.
   *
   * @param commands the commands to include in this group.
   */
  explicit SequentialCommandGroup(
      std::vector<std::shared_ptr<Command>>&& commands);

  /**
   * Creates a new SequentialCommandGroup.  The given commands will be run
   * sequentially, with the CommandGroup finishing when the last command
   * finishes.
   *
   * @param commands the commands to include in this group.
   */
  template <class... Types,
            typename = std::enable_if_t<std::conjunction_v<
                std::is_base_of<Command, std::remove_reference_t<Types>>...>>>
  explicit SequentialCommandGroup(Types&&... commands) {
    AddCommands(std::forward<Types>(commands)...);
  }

  SequentialCommandGroup(SequentialCommandGroup&& other) = default;

  // No copy constructors for command groups
  SequentialCommandGroup(const SequentialCommandGroup&) = delete;

  // Prevent template expansion from emulating copy ctor
  SequentialCommandGroup(SequentialCommandGroup&) = delete;

  template <class... Types,
            typename = std::enable_if_t<std::conjunction_v<
                std::is_base_of<Command, std::remove_reference_t<Types>>...>>>
  void AddCommands(Types&&... commands) {
    std::vector<std::shared_ptr<Command>> foo;
    ((void)foo.emplace_back(std::make_shared<std::remove_reference_t<Types>>(
         std::forward<Types>(commands))),
     ...);
    AddCommands(std::move(foo));
  }

  void Initialize() override;

  void Execute() override;

  void End(bool interrupted) override;

  bool IsFinished() override;

  bool RunsWhenDisabled() const override;

  // std::shared_ptr<Subsystem> BeforeStarting(
  //     std::function<void()> toRun,
  //     wpi::span<std::shared_ptr<Subsystem>> requirements = {})
  //     override;

  // std::shared_ptr<Subsystem> AndThen(
  //     std::function<void()> toRun,
  //     wpi::span<std::shared_ptr<Subsystem>> requirements = {})
  //     override;

 public:
  void AddCommands(std::vector<std::shared_ptr<Command>>&& commands) final;

  wpi::SmallVector<std::shared_ptr<Command>, 4> m_commands;
  size_t m_currentCommandIndex{invalid_index};
  bool m_runWhenDisabled{true};
};


std::shared_ptr<SequentialCommandGroup> SequentialCommandGroup_BeforeStarting(
  std::shared_ptr<SequentialCommandGroup> self,
    std::function<void()> toRun, wpi::span<std::shared_ptr<Subsystem>> requirements);
std::shared_ptr<SequentialCommandGroup> SequentialCommandGroup_AndThen(
    std::shared_ptr<SequentialCommandGroup> self,
    std::function<void()> toRun, wpi::span<std::shared_ptr<Subsystem>> requirements);

}  // namespace frc2

#ifdef _WIN32
#pragma warning(pop)
#endif
