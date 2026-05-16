#!/usr/bin/env python3

import os
from os.path import abspath, dirname
import subprocess
import sys

if __name__ == "__main__":
    root = abspath(dirname(__file__))
    os.chdir(root)

    subprocess.check_call([sys.executable, "-m", "pytest"])
