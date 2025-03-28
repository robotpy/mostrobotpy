#!/usr/bin/env python3
#
# This is a NetworkTables client (eg, the DriverStation/coprocessor side).
# You need to tell it the IP address of the NetworkTables server (the
# robot or simulator).
#
# This is intended to be ran at the same time as the simple_robot.py
# and simple_client.py examples. It will output values as they change.
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

    # Create a poller
    poller = ntcore.NetworkTableListenerPoller(inst)

    # Listen for all connection events
    poller.addConnectionListener(True)

    # Listen to all changes
    msub = ntcore.MultiSubscriber(inst, [""])
    poller.addListener(msub, ntcore.EventFlags.kValueRemote)

    while True:
        # periodically read from the queue
        for event in poller.readQueue():
            print(event)

        time.sleep(1)
