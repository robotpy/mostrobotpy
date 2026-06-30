#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.
#

import wpilib
import wpilib.simulation
import wpimath
import wpimath.units

import constants


class Elevator:
    def __init__(self) -> None:
        # This gearbox represents a gearbox containing 4 Vex 775pro motors.
        self.elevator_gearbox = wpimath.DCMotor.neo(2)

        self.profile = wpimath.ExponentialProfileMeterVolts(
            wpimath.ExponentialProfileMeterVolts.Constraints.from_characteristics(
                constants.K_ELEVATOR_MAX_V,
                constants.K_ELEVATORK_V,
                constants.K_ELEVATORK_A,
            )
        )

        self.setpoint = wpimath.ExponentialProfileMeterVolts.State(0, 0)

        # Standard classes for controlling our elevator
        self.pid_controller = wpimath.PIDController(
            constants.K_ELEVATOR_KP, constants.K_ELEVATOR_KI, constants.K_ELEVATOR_KD
        )

        self.feedforward = wpimath.ElevatorFeedforward(
            constants.K_ELEVATORK_S,
            constants.K_ELEVATORK_G,
            constants.K_ELEVATORK_V,
            constants.K_ELEVATORK_A,
        )
        self.encoder = wpilib.Encoder(
            constants.K_ENCODER_A_CHANNEL, constants.K_ENCODER_B_CHANNEL
        )
        self.motor = wpilib.PWMSparkMax(constants.K_MOTOR_PORT)

        # Simulation classes help us simulate what's going on, including gravity.
        self.elevator_sim = wpilib.simulation.ElevatorSim(
            self.elevator_gearbox,
            constants.K_ELEVATOR_GEARING,
            constants.K_CARRIAGE_MASS,
            constants.K_ELEVATOR_DRUM_RADIUS,
            constants.K_MIN_ELEVATOR_HEIGHT,
            constants.K_MAX_ELEVATOR_HEIGHT,
            True,
            0,
            [0.005, 0.0],
        )
        self.encoder_sim = wpilib.simulation.EncoderSim(self.encoder)
        self.motor_sim = wpilib.simulation.PWMMotorControllerSim(self.motor)

        # Create a Mechanism2d visualization of the elevator
        self.mech2d = wpilib.Mechanism2d(
            wpimath.units.inches_to_meters(10),
            wpimath.units.inches_to_meters(51),
        )
        self.mech_2_d_root = self.mech2d.get_root(
            "Elevator Root",
            wpimath.units.inches_to_meters(5),
            wpimath.units.inches_to_meters(0.5),
        )
        self.elevator_mech_2_d = self.mech_2_d_root.append_ligament(
            "Elevator", self.elevator_sim.get_position(), 90
        )

        # Subsystem constructor.
        self.encoder.set_distance_per_pulse(constants.K_ELEVATOR_ENCODER_DIST_PER_PULSE)

        # Publish Mechanism2d to SmartDashboard
        # To view the Elevator visualization, select Network Tables -> SmartDashboard -> Elevator Sim
        wpilib.SmartDashboard.put_data("Elevator Sim", self.mech2d)

    def simulation_periodic(self) -> None:
        """Advance the simulation."""
        # In this method, we update our simulation of what our elevator is doing
        # First, we set our "inputs" (voltages)
        self.elevator_sim.set_input_voltage(
            self.motor_sim.get_throttle() * wpilib.RobotController.get_battery_voltage()
        )

        # Next, we update it. The standard loop time is 20ms.
        self.elevator_sim.update(0.020)

        # Finally, we set our simulated encoder's readings and simulated battery voltage
        self.encoder_sim.set_distance(self.elevator_sim.get_position())
        # SimBattery estimates loaded battery voltages
        wpilib.simulation.RoboRioSim.set_v_in_voltage(
            wpilib.simulation.BatterySim.calculate([self.elevator_sim.get_current_draw()])
        )

    def reach_goal(self, goal: float) -> None:
        """Run control loop to reach and maintain goal.

        :param goal: the position to maintain
        """
        goal_state = wpimath.ExponentialProfileMeterVolts.State(goal, 0)

        next_state = self.profile.calculate(0.020, self.setpoint, goal_state)

        # With the setpoint value we run PID control like normal
        pid_output = self.pid_controller.calculate(
            self.encoder.get_distance(), self.setpoint.position
        )
        feedforward_output = self.feedforward.calculate(
            self.setpoint.velocity, next_state.velocity
        )

        self.motor.set_voltage(pid_output + feedforward_output)

        self.setpoint = next_state

    def stop(self) -> None:
        """Stop the control loop and motor output."""
        self.motor.set_throttle(0.0)

    def reset(self) -> None:
        """Reset Exponential profile to begin from current position on enable."""
        self.setpoint = wpimath.ExponentialProfileMeterVolts.State(
            self.encoder.get_distance(), 0
        )

    def update_telemetry(self) -> None:
        """Update telemetry, including the mechanism visualization."""
        # Update elevator visualization with position
        self.elevator_mech_2_d.set_length(self.encoder.get_distance())
