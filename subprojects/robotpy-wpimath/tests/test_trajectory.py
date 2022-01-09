from wpimath.trajectory import TrajectoryGenerator
from wpimath.geometry import Transform2d
import wpimath.trajectory
import wpimath.trajectory.constraint

from wpimath.geometry import Pose2d, Rotation2d, Translation2d

from wpimath.trajectory import Trajectory, TrajectoryConfig

from wpimath.trajectory.constraint import (
    MaxVelocityConstraint,
    EllipticalRegionConstraint,
    RectangularRegionConstraint,
)


def getTestTrajectory(config: TrajectoryConfig) -> Trajectory:
    # 2018 cross scale auto waypoints
    sideStart = Pose2d.fromFeet(1.54, 23.23, Rotation2d.fromDegrees(180))
    crossScale = Pose2d.fromFeet(23.7, 6.8, Rotation2d.fromDegrees(-160))

    config.setReversed(True)

    vector = [
        (
            sideStart + Transform2d(Translation2d.fromFeet(-13, 0), Rotation2d())
        ).translation(),
        (
            sideStart
            + Transform2d(
                Translation2d.fromFeet(-19.5, 5.0), Rotation2d.fromDegrees(-90)
            )
        ).translation(),
    ]

    return TrajectoryGenerator.generateTrajectory(sideStart, vector, crossScale, config)


#
# EllipticalRegionConstraint tests
#


def test_elliptical_region_constraint():
    maxVelocity = 2
    config = TrajectoryConfig.fromFps(13, 13)
    maxVelConstraint = MaxVelocityConstraint.fromFps(maxVelocity)
    regionConstraint = EllipticalRegionConstraint.fromFeet(
        Translation2d.fromFeet(5, 2.5),
        10,
        5,
        Rotation2d.fromDegrees(180),
        maxVelConstraint,
    )

    config.addConstraint(regionConstraint)

    trajectory = getTestTrajectory(config)

    exceededConstraintOutsideRegion = False
    for point in trajectory.states():
        translation = point.pose.translation()
        if translation.x_feet < 10 and translation.y_feet < 5:
            assert abs(point.velocity_fps) < maxVelocity + 0.05
        elif abs(point.velocity_fps) >= maxVelocity + 0.05:
            exceededConstraintOutsideRegion = True

    assert exceededConstraintOutsideRegion


def test_elliptical_region_is_pose_in_region():
    maxVelConstraint = MaxVelocityConstraint.fromFps(2)
    regionConstraintNoRotation = EllipticalRegionConstraint.fromFeet(
        Translation2d.fromFeet(1, 1), 2, 4, Rotation2d(0), maxVelConstraint
    )

    assert not regionConstraintNoRotation.isPoseInRegion(Pose2d.fromFeet(2.1, 1, 0))


#
# RectangularRegionConstraint tests
#


def test_rectangular_region_constraint():
    maxVelocity = 2
    config = TrajectoryConfig.fromFps(13, 13)
    maxVelConstraint = MaxVelocityConstraint.fromFps(maxVelocity)
    regionConstraint = RectangularRegionConstraint(
        Translation2d.fromFeet(1, 1),
        Translation2d.fromFeet(5, 27),
        maxVelConstraint,
    )

    config.addConstraint(regionConstraint)

    trajectory = getTestTrajectory(config)

    exceededConstraintOutsideRegion = False
    for point in trajectory.states():
        if regionConstraint.isPoseInRegion(point.pose):
            assert abs(point.velocity_fps) < maxVelocity + 0.05
        elif abs(point.velocity_fps) >= maxVelocity + 0.05:
            exceededConstraintOutsideRegion = True

    assert exceededConstraintOutsideRegion


def test_rectangular_region_is_pose_in_region():
    maxVelConstraint = MaxVelocityConstraint.fromFps(2)
    regionConstraint = RectangularRegionConstraint(
        Translation2d.fromFeet(1, 1), Translation2d.fromFeet(5, 27), maxVelConstraint
    )
    assert not regionConstraint.isPoseInRegion(Pose2d())
    assert regionConstraint.isPoseInRegion(Pose2d.fromFeet(3, 14.5, Rotation2d()))
