#!/usr/bin/env python3
#
# Uses the CameraServer class to automatically capture video from two USB
# webcams and send it to the FRC dashboard without doing any vision
# processing.
#
# Warning: If you're using this with a python-based robot, do not run this
# in the same program as your robot code!
#

from cscore import CameraServer as CS


def main():
    CS.enable_logging()

    usb1 = CS.start_automatic_capture(dev=0)
    usb2 = CS.start_automatic_capture(dev=1)

    CS.wait_forever()


if __name__ == "__main__":
    # To see messages from networktables, you must setup logging
    import logging

    logging.basicConfig(level=logging.DEBUG)

    # You should uncomment these to connect to the RoboRIO
    # import ntcore
    # nt = ntcore.NetworkTableInstance.getDefault()
    # nt.setServerTeam(XXXX)
    # nt.startClient4(__file__)

    main()
