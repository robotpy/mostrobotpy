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
    CS.enable_logging()

    usb0 = UsbCamera("Camera 0", 0)
    usb1 = UsbCamera("Camera 1", 1)

    server = CS.add_switched_camera("Switched")
    server.set_source(usb0)

    # Use networktables to switch the source
    # -> obviously, you can switch them however you'd like
    def _listener(source, key, value, is_new):
        if str(value) == "0":
            server.set_source(usb0)
        elif str(value) == "1":
            server.set_source(usb1)

    table = ntcore.NetworkTableInstance.get_default().get_table("/CameraPublisher")
    table.put_string("selected", "0")
    table.add_entry_listener(_listener, key="selected")

    CS.wait_forever()


if __name__ == "__main__":
    # To see messages from networktables, you must setup logging
    import logging

    logging.basicConfig(level=logging.DEBUG)

    # You should change this to connect to the RoboRIO
    nt = ntcore.NetworkTableInstance.get_default()
    nt.set_server("localhost")
    nt.start_client4(__file__)

    main()
