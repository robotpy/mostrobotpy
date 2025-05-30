import ctypes
import pathlib


def test_halsim_ws_server():
    # dependencies
    import native.wpihal._init_robotpy_native_wpihal
    import native.wpinet._init_robotpy_native_wpinet

    import halsim_ws.server as base

    loaded = 0
    for fname in (pathlib.Path(base.__file__).parent / "lib").iterdir():
        if fname.is_file() and fname.suffix in (".dll", ".dylib", ".so"):
            ctypes.CDLL(str(fname))
            loaded += 1

    assert loaded
