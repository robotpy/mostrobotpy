#!/usr/bin/env python3

import cscore as cs
from wpiutil import PixelFormat

camera = cs.UsbCamera("usbcam", 0)
camera.set_video_mode(PixelFormat.MJPEG, 320, 240, 30)

mjpeg_server = cs.MjpegServer("httpserver", 8081)
mjpeg_server.set_source(camera)

print("mjpg server listening at http://0.0.0.0:8081")
input("Press enter to exit...")
