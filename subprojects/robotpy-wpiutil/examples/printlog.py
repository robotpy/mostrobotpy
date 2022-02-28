#!/usr/bin/env python3

import argparse
import pathlib

from wpiutil.log import DataLogReader

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    args = parser.parse_args()

    reader = DataLogReader(args.infile)
    for record in reader:
        if record.isStart():
            print(record.getStartData())
        else:
            print(record.getBoolean())
