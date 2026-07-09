#!/usr/bin/env python3
#
# Demonstrates streaming and modifying the image via OpenCV
#


import cscore as cs
import numpy as np
from wpiutil import PixelFormat
import cv2


def main():
    camera = cs.UsbCamera("usbcam", 0)
    camera.set_video_mode(PixelFormat.MJPEG, 320, 240, 30)

    mjpeg_server = cs.MjpegServer("httpserver", 8081)
    mjpeg_server.set_source(camera)

    print("mjpg server listening at http://0.0.0.0:8081")

    cvsink = cs.CvSink("cvsink")
    cvsink.set_source(camera)

    cv_source = cs.CvSource("cvsource", PixelFormat.MJPEG, 320, 240, 30)
    cv_mjpeg_server = cs.MjpegServer("cvhttpserver", 8082)
    cv_mjpeg_server.set_source(cv_source)

    print("OpenCV output mjpg server listening at http://0.0.0.0:8082")

    test = np.zeros(shape=(240, 320, 3), dtype=np.uint8)
    flip = np.zeros(shape=(240, 320, 3), dtype=np.uint8)

    while True:
        time, test = cvsink.grab_frame(test)
        if time == 0:
            print("error:", cvsink.get_error())
            continue

        print("got frame at time", time, test.shape)

        cv2.flip(test, 0, flip)
        cv_source.put_frame(flip)


if __name__ == "__main__":
    main()
