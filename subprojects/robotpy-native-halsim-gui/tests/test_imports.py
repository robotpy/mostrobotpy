import ctypes
import ctypes.util
import sys

import pytest


@pytest.mark.skipif(
    sys.platform == "linux"
    and (not ctypes.util.find_library("X11") or not ctypes.util.find_library("GL")),
    reason="X11 / libGL not installed",
)
def test_import_halsim_gui():
    import native.halsim_gui._init_robotpy_native_halsim_gui
