#!/usr/bin/env python3

import argparse
import time
import wpiutil

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int, help="Local port number")
    parser.add_argument("remoteHost", help="Remote IP address / DNS name")
    parser.add_argument("remotePort", type=int, help="remote port number")
    args = parser.parse_args()

    wpiutil.PortForwarder.getInstance().add(args.port, args.remoteHost, args.remotePort)

    while True:
        time.sleep(1)
