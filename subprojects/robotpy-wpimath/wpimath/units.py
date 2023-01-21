# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.

import math

kInchesPerFoot = 12.0
kMetersPerInch = 0.0254
kSecondsPerMinute = 60
kMillisecondsPerSecond = 1000
kKilogramsPerLb = 0.453592


def metersToFeet(meters: float) -> float:
    """Converts given meters to feet.

    :param meters: The meters to convert to feet.

    :returns: Feet converted from meters.
    """
    return metersToInches(meters) / kInchesPerFoot


def feetToMeters(feet: float) -> float:
    """Converts given feet to meters.

    :param feet: The feet to convert to meters.

    :returns: Meters converted from feet.
    """
    return inchesToMeters(feet * kInchesPerFoot)


def metersToInches(meters: float) -> float:
    """Converts given meters to inches.

    :param meters: The meters to convert to inches.

    :returns: Inches converted from meters.
    """
    return meters / kMetersPerInch


def inchesToMeters(inches: float) -> float:
    """Converts given inches to meters.

    :param inches: The inches to convert to meters.

    :returns: Meters converted from inches.
    """
    return inches * kMetersPerInch


# Converts given degrees to radians.
degreesToRadians = math.radians

# Converts given radians to degrees.
radiansToDegrees = math.degrees


def radiansToRotations(radians: float) -> float:
    """Converts given radians to rotations.

    :param radians: The radians to convert.

    :returns: rotations Converted from radians.
    """
    return radians / math.tau


def degreesToRotations(degrees: float) -> float:
    """Converts given degrees to rotations.

    :param degrees: The degrees to convert.

    :returns: rotations Converted from degrees.
    """
    return degrees / 360


def rotationsToDegrees(rotations: float) -> float:
    """Converts given rotations to degrees.

    :param rotations: The rotations to convert.

    :returns: degrees Converted from rotations.
    """
    return rotations * 360


def rotationsToRadians(rotations: float) -> float:
    """Converts given rotations to radians.

    :param rotations: The rotations to convert.

    :returns: radians Converted from rotations.
    """
    return rotations * math.tau


def rotationsPerMinuteToRadiansPerSecond(rpm: float) -> float:
    """Converts rotations per minute to radians per second.

    :param rpm: The rotations per minute to convert to radians per second.

    :returns: Radians per second converted from rotations per minute.
    """
    return (rpm / kSecondsPerMinute) * math.tau


def radiansPerSecondToRotationsPerMinute(radiansPerSecond: float) -> float:
    """Converts radians per second to rotations per minute.

    :param radiansPerSecond: The radians per second to convert to from rotations per minute.

    :returns: Rotations per minute converted from radians per second.
    """
    return (radiansPerSecond * kSecondsPerMinute) / math.tau


def millisecondsToSeconds(milliseconds: float) -> float:
    """Converts given milliseconds to seconds.

    :param milliseconds: The milliseconds to convert to seconds.

    :returns: Seconds converted from milliseconds.
    """
    return milliseconds / kMillisecondsPerSecond


def secondsToMilliseconds(seconds: float) -> float:
    """Converts given seconds to milliseconds.

    :param seconds: The seconds to convert to milliseconds.

    :returns: Milliseconds converted from seconds.
    """
    return seconds * kMillisecondsPerSecond


def kilogramsToLbs(kilograms: float) -> float:
    """Converts kilograms into lbs (pound-mass).

    :param kilograms: The kilograms to convert to lbs (pound-mass).

    :returns: Lbs (pound-mass) converted from kilograms.
    """
    return kilograms / kKilogramsPerLb


def lbsToKilograms(lbs: float) -> float:
    """Converts lbs (pound-mass) into kilograms.

    :param lbs: The lbs (pound-mass) to convert to kilograms.

    :returns: Kilograms converted from lbs (pound-mass).
    """
    return lbs * kKilogramsPerLb
