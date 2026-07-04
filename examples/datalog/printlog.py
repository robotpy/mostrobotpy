#!/usr/bin/env python3
#
# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.

import argparse
import datetime

from wpilog import DataLogReader

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    args = parser.parse_args()

    reader = DataLogReader(args.infile)

    entries = {}
    for record in reader:
        timestamp = record.get_timestamp() / 1000000
        if record.is_start():
            try:
                data = record.get_start_data()
                print(f"{data} [{timestamp}]")
                if data.entry in entries:
                    print("...DUPLICATE entry ID, overriding")
                entries[data.entry] = data
            except TypeError as e:
                print("Start(INVALID)")
        elif record.is_finish():
            try:
                entry = record.get_finish_entry()
                print(f"Finish({entry}) [{timestamp}]")
                if entry not in entries:
                    print("...ID not found")
                else:
                    del entries[entry]
            except TypeError as e:
                print("Finish(INVALID)")
        elif record.is_set_metadata():
            try:
                data = record.get_set_metadata_data()
                print(f"{data} [{timestamp}]")
                if data.entry not in entries:
                    print("...ID not found")
            except TypeError as e:
                print("SetMetadata(INVALID)")
        elif record.is_control():
            print("Unrecognized control record")
        else:
            print(f"Data({record.get_entry()}, size={record.get_size()}) ", end="")
            entry = entries.get(record.get_entry(), None)
            if entry is None:
                print("<ID not found>")
                continue
            print(f"<name='{entry.name}', type='{entry.type}'> [{timestamp}]")

            try:
                # handle systemTime specially
                if entry.name == "systemTime" and entry.type == "int64":
                    dt = datetime.fromtimestamp(record.get_integer() / 1000000)
                    print(f"  {dt:%Y-%m-%d %H:%M:%S.%f}")
                    continue

                if entry.type == "double":
                    print(f"  {record.get_double()}")
                elif entry.type == "int64":
                    print(f"  {record.get_integer()}")
                elif entry.type == "string" or entry.type == "json":
                    print(f"  '{record.get_string()}'")
                elif entry.type == "boolean":
                    print(f"  {record.get_boolean()}")
                elif entry.type == "boolean[]":
                    arr = record.get_boolean_array()
                    print(f"  {arr}")
                elif entry.type == "double[]":
                    arr = record.get_double_array()
                    print(f"  {arr}")
                elif entry.type == "float[]":
                    arr = record.get_float_array()
                    print(f"  {arr}")
                elif entry.type == "int64[]":
                    arr = record.get_integer_array()
                    print(f"  {arr}")
                elif entry.type == "string[]":
                    arr = record.get_string_array()
                    print(f"  {arr}")
                elif entry.type == "raw":
                    print(f"  {record.get_raw()}")
            except TypeError as e:
                print("  invalid", e)
