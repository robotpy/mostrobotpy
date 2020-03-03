
.. _hal_simulation_package:

This package contains various objects that you can use in your simulation
'physics' code or in unit tests to manipulate the 'real' devices that your
user code.

There are simulated devices for every physical device in WPILib. If you don't
see a physical device simulation object in this package, some devices (such
as gyros or CAN motor controllers) can be interacted with via the generic
:class:`.SimDeviceSim` object instead.

For example, to interact with a :class:`wpilib.AnalogInput`, which has its
own simulation object type associated with it:

.. code-block:: pycon

   >>> import wpilib
   >>> ai = wpilib.AnalogInput(1)
   >>> import hal.simulation
   >>> aiSim = hal.simulation.AnalogInSim(1)
   >>> aiSim.setVoltage(2.5)
   >>> ai.getVoltage()
   2.5

However, a :class:`wpilib.ADXRS450_Gyro` uses a generic simulation device
instead:

.. code-block:: pycon

   >>> import wpilib
   >>> gyro = wpilib.ADXRS450_Gyro()
   >>> import hal.simulation
   >>> gyroSim = hal.simulation.SimDeviceSim("ADXRS450_Gyro[0]")
   >>> angleSim = gyroSim.getDouble("Angle")
   >>> angleSim.value = 42
   >>> gyro.getAngle()
   42.0

If you're not sure which devices or values are available in simulation,
we provide functions you can use to discover them:

.. code-block:: pycon

   >>> import hal.simulation
   >>> hal.simulation.SimDeviceSim.enumerateDevices()
   ['ADXRS450_Gyro[0]']
   >>> gyroSim = hal.simulation.SimDeviceSim("ADXRS450_Gyro[0]")
   >>> gyroSim.enumerateValues()
   [('Angle', False), ('Rate', False)]

For more information on integrating simulation physics into your robot:

* :ref:`Robot Simulator documentation <simulator>`
* :ref:`PyFRC Physics API documentation <physics_model>`
* `Basic physics demo <https://github.com/robotpy/examples/tree/master/physics/src>`_

.. warning:: This package cannot be imported on the RoboRIO