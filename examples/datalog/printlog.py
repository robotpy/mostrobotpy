#!/usr/bin/env python3
#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.

import argparse

from wpilog import DataLogReader

from datalog_struct import ExampleRecord

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--predefined", action="store_true")
    parser.add_argument("infile")
    args = parser.parse_args()

    reader = DataLogReader(args.infile)
    struct_types = (ExampleRecord,) if args.predefined else ()

    for record, entry, value in reader.iter_auto(*struct_types):
        timestamp = record.get_timestamp() / 1_000_000
        name = entry.name if entry is not None else f"entry:{record.get_entry()}"
        advertised_type = entry.type if entry is not None else "unknown"
        print(f"{name} [{advertised_type}] [{timestamp}] {value!r}")
