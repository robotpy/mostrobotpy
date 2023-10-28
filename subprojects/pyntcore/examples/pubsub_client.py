#!/usr/bin/env python3
#
# A client that publishes some synchronized values periodically

import argparse
import os
from os.path import basename
import logging
import time

import ntcore

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("ip", type=str, help="IP address to connect to")
    args = parser.parse_args()

    # Initialize NT4 client
    inst = ntcore.NetworkTableInstance.getDefault()

    identity = f"{basename(__file__)}-{os.getpid()}"
    inst.startClient4(identity)

    inst.setServer(args.ip)

    # publish two values
    table = inst.getTable("data")
    pub1 = table.getDoubleTopic("1").publish()
    pub2 = table.getDoubleTopic("2").publish()

    i = 3

    while True:
        # These values are being published fast than the server is polling
        pub1.set(i)
        pub2.set(i + 100)

        time.sleep(0.5)
        i += 1
