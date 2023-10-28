import logging
import typing

from ._cscore import _setLogger


def enableLogging(level: typing.Optional[int] = None):
    """Enable logging for cscore"""
    if level is None:
        level = logging.DEBUG
    logger = logging.getLogger("cscore")
    _setLogger(lambda lvl, file, line, msg: logger.log(lvl, msg), level)
