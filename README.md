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


Development environment
-----------------------

To install all robotpy packages in [editable mode](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#working-in-development-mode)
first run this to install dependencies:

    ./rdev.sh install-prereqs

Then each time you want to build everything:

    ./rdev.sh develop

For pure python development, you can just edit the files in this repository in-place, and
changes will take effect immediately.

If you are changing C++/wrapper code, you will need to rebuild the package that you are
modifying. You can either run the develop command above (which rebuilds everything) or
rebuild an individual package:

    ./rdev.sh develop NAME

It can be a slow process, see the [semiwrap documentation](https://semiwrap.readthedocs.io/en/stable/tips.html)
for tips to make it more efficient.

Cross Compilation
-----------------

We only support cross-compiling for RoboRIO and raspbian via the WPILib
docker build containers. See `.github/workflows/dist.yml`'s `cross-build`
job for the name of the containers and the steps that must be run inside
the container.

