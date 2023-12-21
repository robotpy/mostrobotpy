mostrobotpy
===========

This repository contains core python libraries that wrap the C++ artifacts of
[allwpilib](https://github.com/wpilibsuite/allwpilib). These libraries are
officially supported for use in the FIRST Robotics Competition.

API Documentation
=================

API documentation is at https://robotpy.readthedocs.io/projects/robotpy/en/latest/

Building RobotPy
================

> [!WARNING]
> It is not recommended for users to build their own copy of RobotPy.
> Instead you should use our prebuilt packages that we publish on PyPI and
> on the WPILib artifactory site. See TODO for details

mostrobotpy consists of many interdependent python packages, which can be
found in the `subprojects` directory. Each subproject can be built like
any other python project, but it is recommended that you use our `rdev.sh`
tool instead.

You must have a working C++ build system and python development headers
installed for your system.

Next install dependencies using pip:

    pip install -r rdev_requirements.txt
    pip install numpy

Then run this command to build all the wheels.

    ./rdev.sh ci run

All the resulting wheels are in `dist`, which can be installed using `pip`.

Cross Compilation
-----------------

We only support cross-compiling for RoboRIO and raspbian via the WPILib
docker build containers. See `.github/workflows/dist.yml`'s `cross-build`
job for the name of the containers and the steps that must be run inside
the container.

