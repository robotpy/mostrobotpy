#!/usr/bin/env python3
#
# This is a NetworkTables client (eg, the DriverStation/coprocessor side).
# You need to tell it the IP address of the NetworkTables server (the
# robot or simulator).
#
# When running, this will continue incrementing the value 'dsTime', and the
# value should be visible to other networktables clients and the robot.
#

import argparse
from os.path import basename
import logging
import time

import ntcore


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--protocol",
        type=int,
        choices=[3, 4],
        help="NT Protocol to use",
        default=4,
    )
    parser.add_argument("ip", type=str, help="IP address to connect to")
    args = parser.parse_args()

    inst = ntcore.NetworkTableInstance.getDefault()

    identity = basename(__file__)
    if args.protocol == 3:
        inst.startClient3(identity)
    else:
        inst.startClient4(identity)

    inst.setServer(args.ip)

    sd = inst.getTable("SmartDashboard")

    i = 0
    while True:
        print("robotTime:", sd.getNumber("robotTime", -1))

        sd.putNumber("dsTime", i)
        time.sleep(1)
        i += 1
