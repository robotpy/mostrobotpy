#!/usr/bin/env python3
#
# Uses the CameraServer class to automatically capture video from two USB
# webcams and send one of them to the dashboard without doing any processing.
# To switch between the cameras, change the /CameraPublisher/selected value in NetworkTables
#
# Warning: If you're using this with a python-based robot, do not run this
# in the same program as your robot code!
#

from cscore import CameraServer as CS
from cscore import UsbCamera
import ntcore


def main():
    CS.enableLogging()

    usb0 = UsbCamera("Camera 0", 0)
    usb1 = UsbCamera("Camera 1", 1)

    server = CS.addSwitchedCamera("Switched")
    server.setSource(usb0)

    # Use networktables to switch the source
    # -> obviously, you can switch them however you'd like
    def _listener(source, key, value, isNew):
        if str(value) == "0":
            server.setSource(usb0)
        elif str(value) == "1":
            server.setSource(usb1)

    table = ntcore.NetworkTableInstance.getDefault().getTable("/CameraPublisher")
    table.putString("selected", "0")
    table.addEntryListener(_listener, key="selected")

    CS.waitForever()


if __name__ == "__main__":
    # To see messages from networktables, you must setup logging
    import logging

    logging.basicConfig(level=logging.DEBUG)

    # You should change this to connect to the RoboRIO
    nt = ntcore.NetworkTableInstance.getDefault()
    nt.setServer("localhost")
    nt.startClient4(__file__)

    main()
