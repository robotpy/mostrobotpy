#!/usr/bin/env python3

import sys
import time

import cscore as cs


def _usage():
    print("Usage: settings.py camera [prop val] ... -- [prop val]", file=sys.stderr)
    print("  Example: settings.py brightness 30 raw_contrast 10", file=sys.stderr)


def main():
    if not hasattr(cs, "UsbCamera"):
        print("ERROR: This platform does not currently have cscore UsbCamera support")
        exit(1)

    if len(sys.argv) < 3:
        _usage()
        exit(1)

    try:
        cid = int(sys.argv[1])
    except ValueError:
        print("ERROR: Expected first argument to be a number, got '%s'" % sys.argv[1])
        _usage()
        exit(2)

    camera = cs.UsbCamera("usbcam", cid)

    # Set prior to connect
    argc = 2
    prop_name = None

    for arg in sys.argv[argc:]:
        argc += 1
        if arg == "--":
            break

        if prop_name is None:
            prop_name = arg
        else:
            try:
                prop_val = int(arg)
            except ValueError:
                camera.get_property(prop_name).set_string(arg)
            else:
                camera.get_property(prop_name).set(prop_val)

            prop_name = None

    # Wait to connect
    while not camera.is_connected():
        time.sleep(0.010)

    # Set rest
    for arg in sys.argv[argc:]:
        if prop_name is None:
            prop_name = arg
        else:
            try:
                prop_val = int(arg)
            except ValueError:
                camera.get_property(prop_name).set_string(arg)
            else:
                camera.get_property(prop_name).set(prop_val)

            prop_name = None

    # Print settings
    print("Properties:")
    for prop in camera.enumerate_properties():
        kind = prop.get_kind()
        if kind == cs.VideoProperty.Kind.BOOLEAN:
            print(
                prop.get_name(),
                "(bool) value=%s default=%s" % (prop.get(), prop.get_default()),
            )
        elif kind == cs.VideoProperty.Kind.INTEGER:
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
        elif kind == cs.VideoProperty.Kind.STRING:
            print(prop.get_name(), "(string):", prop.get_string())
        elif kind == cs.VideoProperty.Kind.ENUM:
            print(prop.get_name(), "(enum): value=%s" % prop.get())
            for i, choice in enumerate(prop.get_choices()):
                if choice:
                    print("    %s: %s" % (i, choice))


if __name__ == "__main__":
    main()
