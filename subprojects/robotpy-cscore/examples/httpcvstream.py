#!/usr/bin/env python3
#
# Demonstrates streaming from a HTTP camera server
#


import cscore as cs
import numpy as np
import cv2


def main():
    camera = cs.HttpCamera("httpcam", "http://localhost:8081/?action=stream")
    camera.setVideoMode(cs.VideoMode.PixelFormat.kMJPEG, 320, 240, 30)

    cvsink = cs.CvSink("cvsink")
    cvsink.setSource(camera)

    cvSource = cs.CvSource("cvsource", cs.VideoMode.PixelFormat.kMJPEG, 320, 240, 30)
    cvMjpegServer = cs.MjpegServer("cvhttpserver", 8083)
    cvMjpegServer.setSource(cvSource)

    print("OpenCV output mjpg server listening at http://0.0.0.0:8083")

    test = np.zeros(shape=(240, 320, 3), dtype=np.uint8)
    flip = np.zeros(shape=(240, 320, 3), dtype=np.uint8)

    while True:
        time, test = cvsink.grabFrame(test)
        if time == 0:
            print("error:", cvsink.getError())
            continue

        print("got frame at time", time, test.shape)

        cv2.flip(test, flipCode=0, dst=flip)
        cvSource.putFrame(flip)


if __name__ == "__main__":
    main()
