// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#include "frc2/command/Command.h"

#include "frc2/command/CommandScheduler.h"
#include "frc2/command/InstantCommand.h"
#include "frc2/command/ParallelCommandGroup.h"
#include "frc2/command/ParallelDeadlineGroup.h"
#include "frc2/command/ParallelRaceGroup.h"
#include "frc2/command/PerpetualCommand.h"
#include "frc2/command/ProxyScheduleCommand.h"
#include "frc2/command/SequentialCommandGroup.h"
#include "frc2/command/WaitCommand.h"
#include "frc2/command/WaitUntilCommand.h"

using namespace frc2;

Command::~Command() {
  // CommandScheduler::GetInstance().Cancel(shared_from_this());
}

// Command::Command(const Command& rhs) : ErrorBase(rhs) {}

// Command& Command::operator=(const Command& rhs) {
//   ErrorBase::operator=(rhs);
//   m_isGrouped = false;
//   return *this;
// }

void Command::Initialize() {}
void Command::Execute() {}
void Command::End(bool interrupted) {}

std::shared_ptr<ParallelRaceGroup> Command::WithTimeout(units::second_t duration) {
  std::vector<std::shared_ptr<Command>> temp;
  temp.emplace_back(std::make_shared<WaitCommand>(duration));
  temp.emplace_back(shared_from_this());
  return std::make_shared<ParallelRaceGroup>(std::move(temp));
}

std::shared_ptr<ParallelRaceGroup> Command::WithInterrupt(std::function<bool()> condition) {
  std::vector<std::shared_ptr<Command>> temp;
  temp.emplace_back(std::make_shared<WaitUntilCommand>(std::move(condition)));
  temp.emplace_back(shared_from_this());
  return std::make_shared<ParallelRaceGroup>(std::move(temp));
}

std::shared_ptr<SequentialCommandGroup> Command::BeforeStarting(
    std::function<void()> toRun,
    std::initializer_list<std::shared_ptr<Subsystem>> requirements) {
  return BeforeStarting(
      std::move(toRun),
      wpi::makeArrayRef(requirements.begin(), requirements.end()));
}

std::shared_ptr<SequentialCommandGroup> Command::BeforeStarting(
    std::function<void()> toRun, wpi::ArrayRef<std::shared_ptr<Subsystem>> requirements) {
  std::vector<std::shared_ptr<Command>> temp;
  temp.emplace_back(
      std::make_shared<InstantCommand>(std::move(toRun), requirements));
  temp.emplace_back(shared_from_this());
  return std::make_shared<SequentialCommandGroup>(std::move(temp));
}

std::shared_ptr<SequentialCommandGroup> Command::AndThen(
    std::function<void()> toRun,
    std::initializer_list<std::shared_ptr<Subsystem>> requirements) {
  return AndThen(
      std::move(toRun),
      wpi::makeArrayRef(requirements.begin(), requirements.end()));
}

std::shared_ptr<SequentialCommandGroup> Command::AndThen(
    std::function<void()> toRun, wpi::ArrayRef<std::shared_ptr<Subsystem>> requirements) {
  std::vector<std::shared_ptr<Command>> temp;
  temp.emplace_back(shared_from_this());
  temp.emplace_back(
      std::make_shared<InstantCommand>(std::move(toRun), requirements));
  return std::make_shared<SequentialCommandGroup>(std::move(temp));
}

std::shared_ptr<PerpetualCommand> Command::Perpetually() {
  return std::make_shared<PerpetualCommand>(shared_from_this());
}

std::shared_ptr<ProxyScheduleCommand> Command::AsProxy() {
  return std::make_shared<ProxyScheduleCommand>(shared_from_this());
}

void Command::Schedule(bool interruptible) {
  CommandScheduler::GetInstance().Schedule(interruptible, shared_from_this());
}

void Command::Cancel() {
  CommandScheduler::GetInstance().Cancel(shared_from_this());
}

bool Command::IsScheduled() {
  return CommandScheduler::GetInstance().IsScheduled(shared_from_this());
}

bool Command::HasRequirement(std::shared_ptr<Subsystem> requirement) const {
  bool hasRequirement = false;
  for (auto&& subsystem : GetRequirements()) {
    hasRequirement |= requirement == subsystem;
  }
  return hasRequirement;
}

std::string Command::GetName() const {
  return GetTypeName(shared_from_this());
}

bool Command::IsGrouped() const {
  return m_isGrouped;
}

void Command::SetGrouped(bool grouped) {
  m_isGrouped = grouped;
}

namespace frc2 {
bool RequirementsDisjoint(Command* first, Command* second) {
  bool disjoint = true;
  auto&& requirements = second->GetRequirements();
  for (auto&& requirement : first->GetRequirements()) {
    // disjoint &= requirements.count(requirement) == requirements.end();
    disjoint &= requirements.count(requirement) == 0;
  }
  return disjoint;
}
}  // namespace frc2
