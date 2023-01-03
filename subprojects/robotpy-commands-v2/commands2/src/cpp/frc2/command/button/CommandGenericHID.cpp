// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#include "frc2/command/button/CommandGenericHID.h"

using namespace frc2;

#define loop (loop_arg ? *loop_arg : CommandScheduler::GetInstance().GetDefaultButtonLoop())

Trigger CommandGenericHID::Button(int button, std::optional<frc::EventLoop*> loop_arg) const {
  return GenericHID::Button(button, loop).CastTo<Trigger>();
}

Trigger CommandGenericHID::POV(int angle, std::optional<frc::EventLoop*> loop_arg) const {
  return POV(0, angle, loop);
}

Trigger CommandGenericHID::POV(int pov, int angle, std::optional<frc::EventLoop*> loop_arg) const {
  return Trigger(loop,
                 [this, pov, angle] { return this->GetPOV(pov) == angle; });
}

Trigger CommandGenericHID::POVUp(std::optional<frc::EventLoop*> loop_arg) const {
  return POV(0, loop);
}

Trigger CommandGenericHID::POVUpRight(std::optional<frc::EventLoop*> loop_arg) const {
  return POV(45, loop);
}

Trigger CommandGenericHID::POVRight(std::optional<frc::EventLoop*> loop_arg) const {
  return POV(90, loop);
}

Trigger CommandGenericHID::POVDownRight(std::optional<frc::EventLoop*> loop_arg) const {
  return POV(135, loop);
}

Trigger CommandGenericHID::POVDown(std::optional<frc::EventLoop*> loop_arg) const {
  return POV(180, loop);
}

Trigger CommandGenericHID::POVDownLeft(std::optional<frc::EventLoop*> loop_arg) const {
  return POV(225, loop);
}

Trigger CommandGenericHID::POVLeft(std::optional<frc::EventLoop*> loop_arg) const {
  return POV(270, loop);
}

Trigger CommandGenericHID::POVUpLeft(std::optional<frc::EventLoop*> loop_arg) const {
  return POV(315, loop);
}

Trigger CommandGenericHID::POVCenter(std::optional<frc::EventLoop*> loop_arg) const {
  return POV(360, loop);
}

Trigger CommandGenericHID::AxisLessThan(int axis, double threshold,
                                        std::optional<frc::EventLoop*> loop_arg) const {
  return Trigger(loop, [this, axis, threshold]() {
    return this->GetRawAxis(axis) < threshold;
  });
}

Trigger CommandGenericHID::AxisGreaterThan(int axis, double threshold,
                                           std::optional<frc::EventLoop*> loop_arg) const {
  return Trigger(loop, [this, axis, threshold]() {
    return this->GetRawAxis(axis) > threshold;
  });
}
