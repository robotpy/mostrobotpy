#!/usr/bin/env python3
#
# Uses the CameraServer class to automatically capture video from a USB webcam
# and send it to the FRC dashboard without doing any vision processing.
#
# Warning: If you're using this with a python-based robot, do not run this
# in the same program as your robot code!
#


from cscore import CameraServer


def main():
    cs = CameraServer.getInstance()
    cs.enableLogging()

    cs.startAutomaticCapture()
    cs.waitForever()


if __name__ == "__main__":

    # To see messages from networktables, you must setup logging
    import logging

    logging.basicConfig(level=logging.DEBUG)

    # You should uncomment these to connect to the RoboRIO
    # import networktables
    # networktables.initialize(server='10.xx.xx.2')

    main()
