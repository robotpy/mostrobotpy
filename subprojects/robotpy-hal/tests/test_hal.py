import hal


def test_hal_simdevice():
    device = hal.SimDevice("deviceName")
    v = device.createInt("i", 0, 1)
    assert v.get() == 1
    assert v.type == hal.Type.INT

    v.set(4)
    assert v.get() == 4


def test_hal_send_error(capsys):
    hal._wpiHal.__test_senderr()
    cap = capsys.readouterr()
    assert cap.err == "Error at location: �badmessage\ncallstack\n\n"
