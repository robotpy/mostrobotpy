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
    inst = ntcore.NetworkTableInstance.get_default()

    identity = f"{basename(__file__)}-{os.getpid()}"
    inst.start_client_4(identity)

    inst.set_server(args.ip)

    # publish two values
    table = inst.get_table("data")
    pub1 = table.get_double_topic("1").publish()
    pub2 = table.get_double_topic("2").publish()

    i = 3

    while True:
        # These values are being published fast than the server is polling
        pub1.set(i)
        pub2.set(i + 100)

        time.sleep(0.5)
        i += 1
