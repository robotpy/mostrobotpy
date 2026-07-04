import logging
import typing

from ._cscore import _set_logger


def enable_logging(level: typing.Optional[int] = None):
    """Enable logging for cscore"""
    if level is None:
        level = logging.DEBUG
    logger = logging.getLogger("cscore")
    _set_logger(lambda lvl, file, line, msg: logger.log(lvl, msg), level)
