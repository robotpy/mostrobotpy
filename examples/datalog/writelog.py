#!/usr/bin/env python3

import argparse
import pathlib
import time

import wpilog

from datalog_struct import ExampleRecord


def _wait_for_complete_log(candidate_paths):
    deadline = time.monotonic() + 5
    while True:
        for path in candidate_paths():
            try:
                values = wpilog.DataLogReader(str(path)).iter_auto(ExampleRecord)
                record_count = sum(
                    entry is not None and entry.name == "/record"
                    for _, entry, _ in values
                )
            except (OSError, ValueError):
                continue
            if record_count == 2:
                return

        if time.monotonic() >= deadline:
            raise TimeoutError("timed out waiting for the data log to flush")
        time.sleep(0.01)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("out", type=pathlib.Path)
    args = parser.parse_args()

    if args.out.is_dir():
        existing_paths = set(args.out.iterdir())
        datalog = wpilog.DataLogBackgroundWriter(str(args.out))

        def candidate_paths():
            return set(args.out.iterdir()) - existing_paths

    else:
        datalog = wpilog.DataLogBackgroundWriter(str(args.out.parent), args.out.name)

        def candidate_paths():
            return (args.out,)

    completed = False
    try:
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
        completed = True
    finally:
        try:
            if completed:
                datalog.flush()
                _wait_for_complete_log(candidate_paths)
        finally:
            datalog.stop()
