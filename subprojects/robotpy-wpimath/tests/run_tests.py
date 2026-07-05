#!/usr/bin/env python3

import os
from os.path import abspath, dirname
import sys
import subprocess

if __name__ == "__main__":
    root = abspath(dirname(__file__))
    os.chdir(root)

    args = []
    if sys.platform == "win32":
        # MSVC doesn't directly support c++23 yet
        args = ["--config-settings=setup-args=-Dcpp_std=c++23,c++latest"]

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "--disable-pip-version-check",
            "install",
            "-v",
            "--force-reinstall",
            "--no-build-isolation",
            "./cpp",
        ]
        + args,
    )

    subprocess.check_call([sys.executable, "-m", "pytest", "--ignore=cpp"])
