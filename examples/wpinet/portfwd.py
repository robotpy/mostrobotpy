#!/usr/bin/env python3

import argparse
import time
import wpinet

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int, help="Local port number")
    parser.add_argument("remote_host", help="Remote IP address / DNS name")
    parser.add_argument("remote_port", type=int, help="remote port number")
    args = parser.parse_args()

    wpinet.PortForwarder.get_instance().add(args.port, args.remote_host, args.remote_port)

    while True:
        time.sleep(1)
