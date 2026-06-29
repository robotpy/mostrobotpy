#!/usr/bin/env python3
#
# Demonstrates streaming from a HTTP camera server
#


import cscore as cs
import numpy as np
import cv2


def main():
    camera = cs.HttpCamera("httpcam", "http://localhost:8081/?action=stream")
    camera.set_video_mode(cs.VideoMode.PixelFormat.K_MJPEG, 320, 240, 30)

    cvsink = cs.CvSink("cvsink")
    cvsink.set_source(camera)

    cv_source = cs.CvSource("cvsource", cs.VideoMode.PixelFormat.K_MJPEG, 320, 240, 30)
    cv_mjpeg_server = cs.MjpegServer("cvhttpserver", 8083)
    cv_mjpeg_server.set_source(cv_source)

    print("OpenCV output mjpg server listening at http://0.0.0.0:8083")

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
