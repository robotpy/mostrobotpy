# Copyright (c) FIRST and other WPILib contributors.
# Open Source Software; you can modify and/or share it under the terms of
# the WPILib BSD license file in the root directory of this project.

import pytest

from wpilib import AddressableLEDBuffer, Color, Color8Bit

AddressableLEDBufferView = AddressableLEDBuffer.View


class TestAddressableLEDBuffer:
    """Tests for AddressableLEDBuffer"""

    @pytest.mark.parametrize(
        "h,s,v,r,g,b",
        [
            (0, 0, 0, 0, 0, 0),  # Black
            (0, 0, 255, 255, 255, 255),  # White
            (0, 255, 255, 255, 0, 0),  # Red
            (60, 255, 255, 0, 255, 0),  # Lime
            (120, 255, 255, 0, 0, 255),  # Blue
            (30, 255, 255, 255, 255, 0),  # Yellow
            (90, 255, 255, 0, 255, 255),  # Cyan
            (150, 255, 255, 255, 0, 255),  # Magenta
            (0, 0, 191, 191, 191, 191),  # Silver
            (0, 0, 128, 128, 128, 128),  # Gray
            (0, 255, 128, 128, 0, 0),  # Maroon
            (30, 255, 128, 128, 128, 0),  # Olive
            (60, 255, 128, 0, 128, 0),  # Green
            (150, 255, 128, 128, 0, 128),  # Purple
            (90, 255, 128, 0, 128, 128),  # Teal
            (120, 255, 128, 0, 0, 128),  # Navy
        ],
    )
    def test_hsv_convert(self, h, s, v, r, g, b):
        """Test HSV to RGB conversion"""
        buffer = AddressableLEDBuffer(length=1)
        buffer.setHSV(0, h, s, v)
        color = buffer.getLED8Bit(0)
        assert color.red == r, "R value didn't match"
        assert color.green == g, "G value didn't match"
        assert color.blue == b, "B value didn't match"

    def test_get_color(self):
        """Test getting colors from buffer"""
        buffer = AddressableLEDBuffer(4)
        denim_color_8bit = Color8Bit(Color.kDenim)
        first_blue_color_8bit = Color8Bit(Color.kFirstBlue)
        first_red_color_8bit = Color8Bit(Color.kFirstRed)

        buffer.setLED(0, Color.kFirstBlue)
        buffer.setLED(1, denim_color_8bit)
        buffer.setLED(2, Color.kFirstRed)
        buffer.setLED(3, Color.kFirstBlue)

        assert buffer.getLED(0) == Color.kFirstBlue
        assert buffer.getLED(1) == Color.kDenim
        assert buffer.getLED(2) == Color.kFirstRed
        assert buffer.getLED(3) == Color.kFirstBlue
        assert buffer.getLED8Bit(0) == first_blue_color_8bit
        assert buffer.getLED8Bit(1) == denim_color_8bit
        assert buffer.getLED8Bit(2) == first_red_color_8bit
        assert buffer.getLED8Bit(3) == first_blue_color_8bit

    def test_get_red(self):
        """Test getting red component"""
        buffer = AddressableLEDBuffer(1)
        buffer.setRGB(0, 127, 128, 129)
        assert buffer.getRed(0) == 127

    def test_get_green(self):
        """Test getting green component"""
        buffer = AddressableLEDBuffer(1)
        buffer.setRGB(0, 127, 128, 129)
        assert buffer.getGreen(0) == 128

    def test_get_blue(self):
        """Test getting blue component"""
        buffer = AddressableLEDBuffer(1)
        buffer.setRGB(0, 127, 128, 129)
        assert buffer.getBlue(0) == 129

    def test_iteration(self):
        buffer = AddressableLEDBuffer(3)
        buffer.setRGB(0, 1, 2, 3)
        buffer.setRGB(1, 4, 5, 6)
        buffer.setRGB(2, 7, 8, 9)

        results = []

        for led in buffer:
            results.append((led.r, led.g, led.b))

        assert len(results) == 3
        assert results[0] == (1, 2, 3)
        assert results[1] == (4, 5, 6)
        assert results[2] == (7, 8, 9)

    def test_iteration_on_empty_buffer(self):
        buffer = AddressableLEDBuffer(0)

        for led in buffer:
            assert False, "Iterator should not return items on an empty buffer"


class TestAddressableLEDBufferView:
    """Tests for AddressableLEDBufferView"""

    def test_single_led(self):
        """Test setting a single LED through a view"""
        buffer = AddressableLEDBuffer(10)
        view = buffer[5:6]
        color = Color.kAqua
        view.setLED(0, color)
        assert buffer.getLED(5) == color
        assert view.getLED(0) == color

    def test_segment(self):
        """Test segment view"""
        buffer = AddressableLEDBuffer(10)
        view = buffer[2:9]
        view.setLED(0, Color.kAqua)
        assert buffer.getLED(2) == Color.kAqua

        view.setLED(6, Color.kAzure)
        assert buffer.getLED(8) == Color.kAzure

    @pytest.mark.skip("reversed views are not implemented")
    def test_manual_reversed(self):
        """Test manually reversed view"""
        buffer = AddressableLEDBuffer(10)
        view = buffer[8:1:-1]

        # LED 0 in the view should write to LED 8 on the real buffer
        view.setLED(0, Color.kAqua)
        assert buffer.getLED(8) == Color.kAqua

        # LED 6 in the view should write to LED 2 on the real buffer
        view.setLED(6, Color.kAzure)
        assert buffer.getLED(2) == Color.kAzure

    @pytest.mark.skip("reversed views are not implemented")
    def test_full_manual_reversed(self):
        """Test full manual reversed view"""
        buffer = AddressableLEDBuffer(10)
        view = buffer[9::-1]
        view.setLED(0, Color.kWhite)
        assert buffer.getLED(9) == Color.kWhite

        buffer.setLED(8, Color.kRed)
        assert view.getLED(1) == Color.kRed

    @pytest.mark.skip("reversed views are not implemented")
    def test_reversed(self):
        """Test reversed view"""
        buffer = AddressableLEDBuffer(10)
        view = buffer[:].reversed()
        view.setLED(0, Color.kWhite)
        assert buffer.getLED(9) == Color.kWhite

        view.setLED(9, Color.kRed)
        assert buffer.getLED(0) == Color.kRed
