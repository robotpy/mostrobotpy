.. _wpilib_api:

WPILib API
----------

.. toctree::
  :maxdepth: 1

  wpilib
  wpilib.cameraserver
  wpilib.counter
  wpilib.deployinfo
  wpilib.drive
  wpilib.event
  wpilib.interfaces
  wpilib.shuffleboard
  wpilib.simulation
  wpilib.sysid

.. _ntcore_api:

NTCore API
----------

.. toctree::
  :maxdepth: 1

  ntcore
  ntcore.meta
  ntcore.util

.. _cscore_api:

CSCore API
----------

.. toctree::
  :maxdepth: 1
    
  cscore
  cscore.imagewriter

.. _robotpy_apriltag_api:

Apriltag API
------------

.. toctree::
  :maxdepth: 1

  robotpy_apriltag

.. _wpimath_api:

WPIMath API
-----------

WPIMath provides a comprehensive set of mathematical functions and utilities
tailored to the needs of robotics applications. 

.. toctree::
  :maxdepth: 1

  wpimath
  wpimath.controller
  wpimath.estimator
  wpimath.filter
  wpimath.geometry
  wpimath.interpolation
  wpimath.kinematics
  wpimath.optimization
  wpimath.path
  wpimath.spline
  wpimath.system
  wpimath.system.plant
  wpimath.trajectory
  wpimath.trajectory.constraint
  wpimath.units

.. _wpinet_api:

WPINet API
------------

.. toctree::
  :maxdepth: 1

  wpinet

.. _wpiutil_api:

WPIUtil API
-----------

The C++ version of the WPIUtil library contains various utilities that
user code and WPILib can use to accomplish common tasks that aren't 
necessarily provided by the C++ standard library.

Much of the content in WPIUtil is not useful for Python teams, so we
don't provide access to most of WPIUtil directly. Luckily, RobotPy teams have
access to the full Python standard library, which has many of the same types
of things in it.

.. toctree::
  :maxdepth: 1

  wpiutil
  wpiutil.log
  wpiutil.sync
  wpiutil.wpistruct


.. _hal_api:

HAL API 
-------

The WPILib Hardware Abstraction Layer (HAL) is used by WPILib to interact
with robot devices in a platform independent way.

Generally, RobotPy users should avoid interacting with the HAL directly.

.. toctree::
  :maxdepth: 1

  hal
  hal.simulation
