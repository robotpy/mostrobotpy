#!/usr/bin/env python3

import os
from os.path import abspath, dirname
import sys
import subprocess

if __name__ == "__main__":

    root = abspath(dirname(__file__))
    os.chdir(root)

    env = os.environ.copy()
    env["SETUPTOOLS_SCM_PRETEND_VERSION"] = "0.0.1"

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "--disable-pip-version-check",
            "install",
            "--no-build-isolation",
            "-e",
            "cpp",
        ],
        env=env,
    )

    subprocess.check_call([sys.executable, "-m", "py.test"])
