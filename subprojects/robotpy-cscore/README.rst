robotpy-cscore
==============

These are python bindings for the cscore library, which is a high performance 
library used in the FIRST Robotics competition to serve video to/from robots.
However, the core library is suitable for use in other applications, and is
comparable to something like mjpg-streamer.

This library has only been tested with Python 3, and will most likely not work
with Python 2.7. We do not intend to support using Python 2.7.

.. note:: This is currently a preview release, a stable release with precompiled
          binaries and the like will be available at the end of January. Please
          try this out, file bugs, and make pull requests!

Limitations
===========

The cscore library currently only supports USB cameras on Linux. On other
platforms you will want to use OpenCV to open a VideoCamera object. You can
check at runtime to see if cscore is compiled with USB camera support by
checking for the presence of a 'UsbCamera' class. If it's not there, it's
not supported.

See the `cvstream.py` example for using OpenCV in this manner.

Quick usage
===========

The following will launch a USB Webcam server locally that can be queried via
NetworkTables::

    python3 -m cscore

RoboRIO usage
=============

TODO

Compilation
===========

Currently, this isn't setup to work on Windows. It might work on Windows though,
I haven't tried it yet.

Important: You MUST compile OpenCV with shared libraries (the default), if your
python cv2 is statically linked this will most likely not work with it (if you
do get such a setup working , please let me know!).

Requirements
------------

* Python 3.x
* OpenCV 3.x
* NumPy
* pybind11

You should be able to install numpy and pybind11 via pip:

    pip3 install numpy pybind11
    
You cannot use opencv-python at this time (see notes below), you will need to
compile it from source yourself.

Installation
------------

Once you get OpenCV and NumPy installed, then you should be able to do a::
    
    pip3 install --pre robotpy-cscore
    
If you're installing from the source in this repository, you will need to do:

    git clone https://github.com/robotpy/robotpy-cscore.git
    cd robotpy-cscore
    git submodule init
    git submodule update
    pip3 install .
    
Notes
=====

Long term, I'd like to get this working with opencv-python. However, that's
going to take a bit of work. To track the primary problem related to this, see
https://github.com/skvark/opencv-python/issues/22

Author
======

Dustin Spicuzza (dustin@virtualroadside.com)
