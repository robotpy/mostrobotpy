

import argparse
import importlib.machinery
import os
import logging
from os.path import abspath, basename, dirname, splitext
import signal
import stat
import sys
import threading

from networktables import NetworkTables

log_datefmt = "%H:%M:%S"
log_format = "%(asctime)s:%(msecs)03d %(levelname)-8s: %(name)-20s: %(message)s"

_raise_kb = True

def _parent_poll_thread():
    '''Kills process if input disappears'''
    try:
        while True:
            if not sys.stdin.read():
                break
    except Exception:
        pass
    
    global _raise_kb
    _raise_kb = False
    
    os.kill(os.getpid(), signal.SIGINT)


def main():
    
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="Enable debug logging")
    nt_server_group = parser.add_mutually_exclusive_group()
    nt_server_group.add_argument('--robot', help="Robot's IP address", default='127.0.0.1')
    nt_server_group.add_argument('--team', help='Team number to specify robot', type=int)
    parser.add_argument('vision_py', nargs='?',
                        help='A string indicating the filename and object/function to call'
                             ' (ex: vision.py:main)')
    
    args = parser.parse_args()
    
    # initialize logging first
    log_level = logging.DEBUG if args.verbose else logging.INFO

    logging.basicConfig(datefmt=log_datefmt,
                        format=log_format,
                        level=log_level)

    # Enable cscore python logging
    from ._logging import enableLogging
    enableLogging(level=log_level)
    logger = logging.getLogger('cscore')
    
    # Initialize NetworkTables next
    if args.team:
        NetworkTables.startClientTeam(args.team)
    else:
        NetworkTables.initialize(server=args.robot)
    
    # If stdin is a pipe, then die when the pipe goes away
    # -> this allows us to detect if a parent process exits
    if stat.S_ISFIFO(os.fstat(0).st_mode):
        t = threading.Thread(target=_parent_poll_thread)
        t.daemon = True
        t.start()
        
    global _raise_kb
    
    try:
    
        # If no python file specified, then just start the automatic capture
        if args.vision_py is None:
            from .cameraserver import CameraServer
            cs = CameraServer.getInstance()
            cs.startAutomaticCapture()
            cs.waitForever()
            
        else:
            s = args.vision_py.split(':', 1)
            vision_py = abspath(s[0])
            vision_fn = 'main' if len(s) == 1 else s[1]
            
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
                if hasattr(obj, 'process'):
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
                
    except KeyboardInterrupt:
        if _raise_kb:
            raise
    finally:
        logger.warning("cscore exiting")

if __name__ == '__main__':
    main()
