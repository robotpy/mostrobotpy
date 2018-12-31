#!/usr/bin/env python3

import cscore as cs


def main():
    for caminfo in cs.UsbCamera.enumerateUsbCameras():
        print("%s: %s (%s)" % (caminfo.dev, caminfo.path, caminfo.name))
        if caminfo.otherPaths:
            print("Other device paths:")
            for path in caminfo.otherPaths:
                print(" ", path)

        camera = cs.UsbCamera("usbcam", caminfo.dev)

        print("Properties:")
        for prop in camera.enumerateProperties():
            kind = prop.getKind()
            if kind == cs.VideoProperty.Kind.kBoolean:
                print(
                    prop.getName(),
                    "(bool) value=%s default=%s" % (prop.get(), prop.getDefault()),
                )
            elif kind == cs.VideoProperty.Kind.kInteger:
                print(
                    prop.getName(),
                    "(int): value=%s min=%s max=%s step=%s default=%s"
                    % (
                        prop.get(),
                        prop.getMin(),
                        prop.getMax(),
                        prop.getStep(),
                        prop.getDefault(),
                    ),
                )
            elif kind == cs.VideoProperty.Kind.kString:
                print(prop.getName(), "(string):", prop.getString())
            elif kind == cs.VideoProperty.Kind.kEnum:
                print(prop.getName(), "(enum): value=%s" % prop.get())
                for i, choice in enumerate(prop.getChoices()):
                    if choice:
                        print("    %s: %s" % (i, choice))

        print("Video Modes")
        for mode in camera.enumerateVideoModes():
            if mode.pixelFormat == cs.VideoMode.PixelFormat.kMJPEG:
                fmt = "MJPEG"
            elif mode.pixelFormat == cs.VideoMode.PixelFormat.kYUYV:
                fmt = "YUYV"
            elif mode.pixelFormat == cs.VideoMode.PixelFormat.kRGB565:
                fmt = "RGB565"
            else:
                fmt = "Unknown"

            print("  PixelFormat:", fmt)
            print("   Width:", mode.width)
            print("   Height:", mode.height)
            print("   FPS: ", mode.fps)


if __name__ == "__main__":
    main()
