#!/usr/bin/env python3

import argparse
import pathlib

import wpilog

from datalog_struct import ExampleRecord

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=pathlib.Path)
    args = parser.parse_args()

    if args.out.is_dir():
        datalog = wpilog.DataLogBackgroundWriter(str(args.out))
    else:
        datalog = wpilog.DataLogBackgroundWriter(str(args.out.parent), args.out.name)

    bools = wpilog.BooleanLogEntry(datalog, "/bools")
    bools.append(True)
    bools.append(False)

    strings = wpilog.StringArrayLogEntry(datalog, "/strings")
    strings.append(["a", "b", "c"])
    strings.append(["d", "e", "f"])

    raw = wpilog.RawLogEntry(datalog, "/raws")
    raw.append(b"\x01\x02\x03")
    raw.append(b"\x04\x05\x06")

    record = wpilog.StructLogEntry(datalog, "/record", ExampleRecord)
    record.append(ExampleRecord(1, 2))
    record.append(ExampleRecord(3, 4))
