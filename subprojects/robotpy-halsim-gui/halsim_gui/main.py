import logging
import os
from os.path import abspath, dirname, join

logger = logging.getLogger("halsim_gui")


class HalSimGuiMain:
    """
        Runs the robot using WPILib's GUI HAL Simulator
    """

    def __init__(self, parser):
        pass

    def run(self, options, robot_class, **static_options):

        try:
            import hal
        except ImportError:
            # really, should never happen...
            raise ImportError("you must install robotpy-hal!")

        from .version import version

        logger.info("WPILib HAL Simulation %s", version)

        root = join(abspath(dirname(__file__)), "lib")
        ext = join(root, os.listdir(root)[0])
        retval = hal.loadOneExtension(ext)
        if retval != 0:
            logger.warn("loading extension may have failed (error=%d)", retval)

        return robot_class.main(robot_class)
