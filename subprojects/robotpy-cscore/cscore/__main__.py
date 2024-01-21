import argparse
import importlib.machinery
import os
import logging
from os.path import abspath, basename, dirname, splitext
import stat
import sys
import threading

from ntcore import NetworkTableInstance

log_datefmt = "%H:%M:%S"
log_format = "%(asctime)s:%(msecs)03d %(levelname)-8s: %(name)-20s: %(message)s"

logger = logging.getLogger("cscore")


def _parent_poll_thread() -> None:
    """Kills process if input disappears"""
    from ._cscore import stopMainRunLoop

    try:
        while True:
            if not sys.stdin.read():
                break
    except Exception:
        pass

    stopMainRunLoop()


def _run_user_thread(vision_py: str, vision_fn: str) -> None:
    vision_pymod = splitext(basename(vision_py))[0]

    logger.info("Loading %s (%s)", vision_py, vision_fn)

    sys.path.insert(0, dirname(vision_py))

    loader = importlib.machinery.SourceFileLoader(vision_pymod, vision_py)
    vision_module = loader.load_module(vision_pymod)

    try:
        obj = getattr(vision_module, vision_fn)

        # If the object has a 'process' function, then we assume
        # that it is a GRIP-generated pipeline, so launch it via the
        # GRIP shim
        if hasattr(obj, "process"):
            logger.info("-> Detected GRIP-compatible object")

            from . import grip

            grip.run(obj)
        else:
            # otherwise just call it
            obj()

    except Exception:
        logger.exception("%s exited unexpectedly", vision_py)
    finally:
        logger.warning("%s exited", vision_py)

        from ._cscore import stopMainRunLoop

        stopMainRunLoop()


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable debug logging",
    )
    nt_server_group = parser.add_mutually_exclusive_group()
    nt_server_group.add_argument(
        "--robot", help="Robot's IP address", default="127.0.0.1"
    )
    nt_server_group.add_argument(
        "--team", help="Team number to specify robot", type=int
    )
    parser.add_argument(
        "--nt-protocol",
        choices=[3, 4],
        type=int,
        help="NetworkTables protocol",
        default=4,
    )
    parser.add_argument(
        "--nt-identity", default="cscore", help="NetworkTables identity"
    )
    parser.add_argument(
        "vision_py",
        nargs="?",
        help="A string indicating the filename and object/function to call"
        " (ex: vision.py:main)",
    )

    args = parser.parse_args()

    # initialize logging first
    log_level = logging.DEBUG if args.verbose else logging.INFO

    logging.basicConfig(datefmt=log_datefmt, format=log_format, level=log_level)

    # Enable cscore python logging
    from ._logging import enableLogging

    enableLogging(level=log_level)

    # Initialize NetworkTables next
    ntinst = NetworkTableInstance.getDefault()
    if args.team:
        ntinst.setServerTeam(args.team)
    else:
        ntinst.setServer(args.robot)

    if args.nt_protocol == 3:
        ntinst.startClient3(args.nt_identity)
    else:
        ntinst.startClient4(args.nt_identity)

    # If stdin is a pipe, then die when the pipe goes away
    # -> this allows us to detect if a parent process exits
    if stat.S_ISFIFO(os.fstat(0).st_mode):
        t = threading.Thread(target=_parent_poll_thread, name="lifetime", daemon=True)
        t.start()

    # If no python file specified, then just start the automatic capture
    if args.vision_py is None:
        from ._cscore import CameraServer

        CameraServer.startAutomaticCapture()
    else:
        s = args.vision_py.split(":", 1)
        vision_py = abspath(s[0])
        vision_fn = "main" if len(s) == 1 else s[1]

        thread = threading.Thread(
            target=_run_user_thread,
            args=(vision_py, vision_fn),
            name="vision",
            daemon=True,
        )
        thread.start()

    try:
        from ._cscore import runMainRunLoopTimeout

        SIGNALED = 2
        while runMainRunLoopTimeout(1) != SIGNALED:
            pass

    finally:
        logger.warning("cscore exiting")


if __name__ == "__main__":
    # Setup wpi::now on roborio when executed as __main__
    try:
        from ._cscore import _setupWpiNow  # type: ignore

        _setupWpiNow()
    except ImportError:
        pass

    main()
