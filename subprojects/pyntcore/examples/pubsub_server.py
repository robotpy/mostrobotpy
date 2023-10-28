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
    inst = ntcore.NetworkTableInstance.getDefault()
    inst.startServer()

    # Initialize two subscriptions
    table = inst.getTable("data")

    # only keep the latest value for this topic
    sub1 = table.getDoubleTopic("1").subscribe(-1.0)

    # keep the last 10 values for this topic
    sub2 = table.getDoubleTopic("2").subscribe(
        -2.0, ntcore.PubSubOptions(pollStorage=10)
    )

    # Periodically read from them
    # - note sub1 only has 1 value, but sub2 sometimes has more than 1
    while True:
        print("---", ntcore._now())
        print("/data/1:", sub1.readQueue())
        print("/data/2:", sub2.readQueue())

        time.sleep(1.2)
