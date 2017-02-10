
from ._cscore import *
from ._logging import enableLogging

from .cameraserver import CameraServer, VideoException

try:
    from .version import __version__
except ImportError:
    __version__ = 'master'
