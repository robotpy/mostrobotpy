#!/usr/bin/env python3
#
# A server that reads from the subscription
#

import logging
import time

import ntcore

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # initialize networktables server (on a robot this is already done)
    inst = ntcore.NetworkTableInstance.get_default()
    inst.start_server()

    # Initialize two subscriptions
    table = inst.get_table("data")

    # only keep the latest value for this topic
    sub1 = table.get_double_topic("1").subscribe(-1.0)

    # keep the last 10 values for this topic
    sub2 = table.get_double_topic("2").subscribe(
        -2.0, ntcore.PubSubOptions(poll_storage=10)
    )

    # Periodically read from them
    # - note sub1 only has 1 value, but sub2 sometimes has more than 1
    while True:
        print("---", ntcore._now())
        print("/data/1:", sub1.read_queue())
        print("/data/2:", sub2.read_queue())

        time.sleep(1.2)
