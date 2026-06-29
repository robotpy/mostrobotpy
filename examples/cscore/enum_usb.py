#!/usr/bin/env python3

import cscore as cs


def main():
    for caminfo in cs.UsbCamera.enumerate_usb_cameras():
        print("%s: %s (%s)" % (caminfo.dev, caminfo.path, caminfo.name))
        if caminfo.other_paths:
            print("Other device paths:")
            for path in caminfo.other_paths:
                print(" ", path)

        camera = cs.UsbCamera("usbcam", caminfo.dev)

        print("Properties:")
        for prop in camera.enumerate_properties():
            kind = prop.get_kind()
            if kind == cs.VideoProperty.Kind.K_BOOLEAN:
                print(
                    prop.get_name(),
                    "(bool) value=%s default=%s" % (prop.get(), prop.get_default()),
                )
            elif kind == cs.VideoProperty.Kind.K_INTEGER:
                print(
                    prop.get_name(),
                    "(int): value=%s min=%s max=%s step=%s default=%s"
                    % (
                        prop.get(),
                        prop.get_min(),
                        prop.get_max(),
                        prop.get_step(),
                        prop.get_default(),
                    ),
                )
            elif kind == cs.VideoProperty.Kind.K_STRING:
                print(prop.get_name(), "(string):", prop.get_string())
            elif kind == cs.VideoProperty.Kind.K_ENUM:
                print(prop.get_name(), "(enum): value=%s" % prop.get())
                for i, choice in enumerate(prop.get_choices()):
                    if choice:
                        print("    %s: %s" % (i, choice))

        print("Video Modes")
        for mode in camera.enumerate_video_modes():
            if mode.pixel_format == cs.VideoMode.PixelFormat.K_MJPEG:
                fmt = "MJPEG"
            elif mode.pixel_format == cs.VideoMode.PixelFormat.K_YUYV:
                fmt = "YUYV"
            elif mode.pixel_format == cs.VideoMode.PixelFormat.K_RGB_565:
                fmt = "RGB565"
            else:
                fmt = "Unknown"

            print("  PixelFormat:", fmt)
            print("   Width:", mode.width)
            print("   Height:", mode.height)
            print("   FPS: ", mode.fps)


if __name__ == "__main__":
    main()
