#!/usr/bin/env python3
#
# This is a NetworkTables server (eg, the robot or simulator side).
#
# On a real robot, you probably would create an instance of the
# wpilib.SmartDashboard object and use that instead -- but it's really
# just a passthru to the underlying NetworkTable object.
#
# When running, this will continue incrementing the value 'robotTime',
# and the value should be visible to networktables clients such as
# Shuffleboard or simple_client.py
#

import logging
import time

import ntcore


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    inst = ntcore.NetworkTableInstance.getDefault()

    inst.startServer()
    sd = inst.getTable("SmartDashboard")

    i = 0
    while True:
        print("dsTime:", sd.getNumber("dsTime", -1))

        sd.putNumber("robotTime", i)
        time.sleep(1)
        i += 1
