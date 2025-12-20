import wpilib.simulation


def test_wpilib_simulation():
    pass


def test_addressableled_sim():
    sim = wpilib.simulation.AddressableLEDSim.createForIndex(0)
    led = wpilib.AddressableLED(0)
    assert not sim.getRunning()
    led.start()
    assert sim.getRunning()

    data = [
        wpilib.AddressableLED.LEDData(1, 2, 3),
        wpilib.AddressableLED.LEDData(4, 5, 6),
    ]

    led.setLength(len(data))
    led.setData(data)
    assert sim.getData() == data

    led.stop()
    assert not sim.getRunning()
