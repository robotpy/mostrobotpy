#!/usr/bin/env python3
#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

import wpilib
import math

import wpilib.simulation
import wpimath
import wpimath.units


class MyRobot(wpilib.TimedRobot):
    """
    This is a sample program to demonstrate the use of a BangBangController with a flywheel to
    control RPM.
    """

    K_MOTOR_PORT = 0
    K_ENCODER_A_CHANNEL = 0
    K_ENCODER_B_CHANNEL = 1

    # Max setpoint for joystick control in RPM
    K_MAX_SETPOINT_VALUE = 6000.0

    # Gains are for example purposes only - must be determined for your own robot!
    K_FLYWHEEL_KS = 0.0001  # V
    K_FLYWHEEL_KV = 0.000195  # V/RPM
    K_FLYWHEEL_KA = 0.0003  # V/(RPM/s)

    # Reduction between motors and encoder, as output over input. If the flywheel
    # spins slower than the motors, this number should be greater than one.
    K_FLYWHEEL_GEARING = 1.0

    # 1/2 MR²
    K_FLYWHEEL_MOMENT_OF_INERTIA = (
        0.5
        * wpimath.units.lbs_to_kilograms(1.5)
        * math.pow(wpimath.units.inches_to_meters(4), 2)
    )

    def __init__(self) -> None:
        """Robot initialization function"""
        super().__init__()

        self.flywheel_motor = wpilib.PWMSparkMax(self.K_MOTOR_PORT)
        self.encoder = wpilib.Encoder(self.K_ENCODER_A_CHANNEL, self.K_ENCODER_B_CHANNEL)

        self.bang_bang_controler = wpimath.BangBangController()

        # Gains are for example purposes only - must be determined for your own robot!
        self.feedforward = wpimath.SimpleMotorFeedforwardMeters(
            self.K_FLYWHEEL_KS, self.K_FLYWHEEL_KV, self.K_FLYWHEEL_KA
        )

        # Joystick to control setpoint
        self.joystick = wpilib.Joystick(0)

        # Simulation classes help us simulate our robot

        self.gearbox = wpimath.DCMotor.neo(1)

        self.plant = wpimath.Models.flywheel_from_physical_constants(
            self.gearbox, self.K_FLYWHEEL_GEARING, self.K_FLYWHEEL_MOMENT_OF_INERTIA
        )

        self.flywheel_sim = wpilib.simulation.FlywheelSim(self.plant, self.gearbox)
        self.encoder_sim = wpilib.simulation.EncoderSim(self.encoder)

        # Add bang-bang controller to SmartDashboard and networktables.
        wpilib.SmartDashboard.put_data(self.bang_bang_controler)

    def teleop_periodic(self) -> None:
        """Controls flywheel to a set velocity (RPM) controlled by a joystick."""

        # Scale setpoint value between 0 and maxSetpointValue
        setpoint = max(
            0.0,
            self.joystick.get_raw_axis(0)
            * wpimath.units.rotations_per_minute_to_radians_per_second(
                self.K_MAX_SETPOINT_VALUE
            ),
        )

        # Set setpoint and measurement of the bang-bang controller
        bang_output = (
            self.bang_bang_controler.calculate(self.encoder.get_rate(), setpoint) * 12.0
        )

        # Controls a motor with the output of the BangBang controller and a
        # feedforward. The feedforward is reduced slightly to avoid overvelocitying
        # the shooter.
        self.flywheel_motor.set_voltage(
            bang_output + 0.9 * self.feedforward.calculate(setpoint)
        )

    def simulation_periodic(self) -> None:
        """Update our simulation. This should be run every robot loop in simulation."""
        # To update our simulation, we set motor voltage inputs, update the
        # simulation, and write the simulated velocities to our simulated encoder
        self.flywheel_sim.set_input_voltage(
            self.flywheel_motor.get_throttle() * wpilib.RobotController.get_input_voltage()
        )
        self.flywheel_sim.update(0.02)
        self.encoder_sim.set_rate(self.flywheel_sim.get_angular_velocity())
