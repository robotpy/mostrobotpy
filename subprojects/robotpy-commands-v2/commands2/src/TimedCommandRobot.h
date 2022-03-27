
#pragma once

#include <frc/TimedRobot.h>
#include <frc2/command/CommandScheduler.h>

namespace frc2 {

/**
 * TimedCommandRobot implements the IterativeRobotBase robot program framework.
 *
 * The TimedCommandRobot class is intended to be subclassed by a user creating a
 * command-based robot program. This python-specific class calls the
 * CommandScheduler run method in robotPeriodic for you.
 */
class TimedCommandRobot : public frc::TimedRobot {
public:

  TimedCommandRobot(units::second_t period = frc::TimedRobot::kDefaultPeriod) :
    TimedRobot(period)
  {}

  /** Ensures commands are run */
  void RobotPeriodic() override { CommandScheduler::GetInstance().Run(); }
};

}  // namespace frc2