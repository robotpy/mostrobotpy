#pragma once

#include <frc/trajectory/constraint/TrajectoryConstraint.h>
#include <semiwrap.h>

namespace frc {

struct PyTrajectoryConstraint : public TrajectoryConstraint {

  PyTrajectoryConstraint() {}

  units::meters_per_second_t
  MaxVelocity(const Pose2d &pose, units::curvature_t curvature,
              units::meters_per_second_t velocity) const override {
    return m_constraint->MaxVelocity(pose, curvature, velocity);
  }

  MinMax MinMaxAcceleration(const Pose2d &pose, units::curvature_t curvature,
                            units::meters_per_second_t speed) const override {
    return m_constraint->MinMaxAcceleration(pose, curvature, speed);
  }

  std::shared_ptr<TrajectoryConstraint> m_constraint;
};

}; // namespace frc

NAMESPACE_BEGIN(NB_NAMESPACE)
NAMESPACE_BEGIN(detail)

template <> struct type_caster<frc::PyTrajectoryConstraint> {
  using value_conv = make_caster<std::shared_ptr<frc::TrajectoryConstraint>>;

  NB_TYPE_CASTER(frc::PyTrajectoryConstraint,
                 const_name("wpimath._controls._controls.constraint.TrajectoryConstraint"));

  bool from_python(handle src, uint8_t flags, cleanup_list *cleanup) noexcept {
    value_conv conv;
    if (!conv.from_python(src, flags, cleanup)) {
      return false;
    }

    value.m_constraint = (cast_t<std::shared_ptr<frc::TrajectoryConstraint>>) conv;
    return true;
  }

  static handle from_cpp(const frc::PyTrajectoryConstraint &src,
                         rv_policy policy, cleanup_list *cleanup) noexcept {
    return value_conv::from_cpp(src.m_constraint, policy, cleanup);
  }
};

NAMESPACE_END(detail)
NAMESPACE_END(NB_NAMESPACE)
