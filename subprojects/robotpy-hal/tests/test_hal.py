import hal


def test_hal_simdevice():
    device = hal.SimDevice("deviceName")
    v = device.createInt("i", 0, 1)
    assert v.get() == 1
    assert v.type == hal.Type.INT

    v.set(4)
    assert v.get() == 4
