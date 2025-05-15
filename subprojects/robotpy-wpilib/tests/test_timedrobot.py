import pytest

from wpilib.timedrobotpy import _Callback


def test_calcFutureExpirationUs() -> None:
    cb = _Callback(func=None, periodUs=20_000, expirationUs=100)
    assert cb.calcFutureExpirationUs(100) == 20_100
    assert cb.calcFutureExpirationUs(101) == 20_100
    assert cb.calcFutureExpirationUs(20_099) == 20_100
    assert cb.calcFutureExpirationUs(20_100) == 40_100
    assert cb.calcFutureExpirationUs(20_101) == 40_100

    cb = _Callback(func=None, periodUs=40_000, expirationUs=500)
    assert cb.calcFutureExpirationUs(500) == 40_500
    assert cb.calcFutureExpirationUs(501) == 40_500
    assert cb.calcFutureExpirationUs(40_499) == 40_500
    assert cb.calcFutureExpirationUs(40_500) == 80_500
    assert cb.calcFutureExpirationUs(40_501) == 80_500

    cb = _Callback(func=None, periodUs=1_000, expirationUs=0)
    assert (
        cb.calcFutureExpirationUs(1_000_000_000_000_000_000)
        == 1_000_000_000_000_001_000
    )
    assert (
        cb.calcFutureExpirationUs(1_000_000_000_000_000_001)
        == 1_000_000_000_000_001_000
    )
    assert (
        cb.calcFutureExpirationUs(1_000_000_000_000_000_999)
        == 1_000_000_000_000_001_000
    )
    assert (
        cb.calcFutureExpirationUs(1_000_000_000_000_001_000)
        == 1_000_000_000_000_002_000
    )
    assert (
        cb.calcFutureExpirationUs(1_000_000_000_000_001_001)
        == 1_000_000_000_000_002_000
    )
