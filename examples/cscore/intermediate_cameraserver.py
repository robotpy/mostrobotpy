#!/usr/bin/env python3
#
# This is a demo program showing CameraServer usage with OpenCV to do image
# processing. The image is acquired from the USB camera, then a rectangle
# is put on the image and sent to the dashboard. OpenCV has many methods
# for different types of processing.
#
# Warning: If you're using this with a python-based robot, do not run this
# in the same program as your robot code!
#

import cv2
import numpy as np

from cscore import CameraServer as CS


def main():
    CS.enableLogging()

    camera = CS.startAutomaticCapture()

    camera.setResolution(640, 480)

    # Get a CvSink. This will capture images from the camera
    cvSink = CS.getVideo()

    # (optional) Setup a CvSource. This will send images back to the Dashboard
    outputStream = CS.putVideo("Rectangle", 640, 480)

    # Allocating new images is very expensive, always try to preallocate
    img = np.zeros(shape=(480, 640, 3), dtype=np.uint8)

    while True:
        # Tell the CvSink to grab a frame from the camera and put it
        # in the source image.  If there is an error notify the output.
        time, img = cvSink.grabFrame(img)
        if time == 0:
            # Send the output the error.
            outputStream.notifyError(cvSink.getError())
            # skip the rest of the current iteration
            continue

        # Put a rectangle on the image
        cv2.rectangle(img, (100, 100), (400, 400), (255, 255, 255), 5)

        # Give the output stream a new image to display
        outputStream.putFrame(img)


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
