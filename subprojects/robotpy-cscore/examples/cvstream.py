#!/usr/bin/env python3
#
# WARNING: You should only use this approach for testing cscore on platforms that
#          it doesn't support using UsbCamera
#

import cscore as cs

if hasattr(cs, "UsbCamera"):
    camera = cs.UsbCamera("usbcam", 0)
    camera.setVideoMode(cs.VideoMode.PixelFormat.kMJPEG, 320, 240, 30)
else:
    import cv2
    import threading

    camera = cs.CvSource("cvsource", cs.VideoMode.PixelFormat.kMJPEG, 320, 240, 30)

    # tell OpenCV to capture video for us
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    # Do it in another thread
    def _thread():
        img = None
        while True:
            retval, img = cap.read(img)
            if retval:
                camera.putFrame(img)

    th = threading.Thread(target=_thread, daemon=True)
    th.start()


mjpegServer = cs.MjpegServer("httpserver", 8081)
mjpegServer.setSource(camera)

print("mjpg server listening at http://0.0.0.0:8081")
input("Press enter to exit...")
