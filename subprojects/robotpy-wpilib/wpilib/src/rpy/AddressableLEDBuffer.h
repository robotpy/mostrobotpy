// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

#pragma once

#include <vector>
#include "frc/AddressableLED.h"
#include "frc/util/Color.h"
#include "frc/util/Color8Bit.h"

namespace frc {

/**
 * Buffer storage for Addressable LEDs.
 */
class AddressableLEDBuffer {
 public:
  /**
   * Constructs a new LED buffer with the specified length.
   *
   * @param length The length of the buffer in pixels
   */
  explicit AddressableLEDBuffer(size_t length) : m_buffer(length) {}

  /**
   * Sets a specific LED in the buffer.
   *
   * @param index the index to write
   * @param r the r value [0-255]
   * @param g the g value [0-255]
   * @param b the b value [0-255]
   */
  void SetRGB(size_t index, int r, int g, int b) {
    m_buffer.at(index).SetRGB(r, g, b);
  }

  /**
   * Sets a specific LED in the buffer.
   *
   * @param index the index to write
   * @param h the h value [0-180)
   * @param s the s value [0-255]
   * @param v the v value [0-255]
   */
  void SetHSV(size_t index, int h, int s, int v) {
    m_buffer.at(index).SetHSV(h, s, v);
  }

  /**
   * Sets a specific LED in the buffer.
   *
   * @param index the index to write
   * @param color the color to write
   */
  void SetLED(size_t index, const Color& color) {
    m_buffer.at(index).SetLED(color);
  }

  /**
   * Sets a specific LED in the buffer.
   *
   * @param index the index to write
   * @param color the color to write
   */
  void SetLED(size_t index, const Color8Bit& color) {
    m_buffer.at(index).SetLED(color);
  }

  /**
   * Gets the buffer length.
   *
   * @return the buffer length
   */
  size_t size() const { return m_buffer.size(); }

  /**
   * Gets the red value at the specified index.
   *
   * @param index the index
   * @return the red value
   */
  int GetRed(size_t index) const {
    return m_buffer.at(index).r;
  }

  /**
   * Gets the green value at the specified index.
   *
   * @param index the index
   * @return the green value
   */
  int GetGreen(size_t index) const {
    return m_buffer.at(index).g;
  }

  /**
   * Gets the blue value at the specified index.
   *
   * @param index the index
   * @return the blue value
   */
  int GetBlue(size_t index) const {
    return m_buffer.at(index).b;
  }

  /**
   * Gets the color at the specified index.
   *
   * @param index the index
   * @return the LED color
   */
  Color GetLED(size_t index) const {
    const auto& led = m_buffer.at(index);
    return Color{led.r / 255.0, led.g / 255.0, led.b / 255.0};
  }

  /**
   * Gets the color at the specified index.
   *
   * @param index the index
   * @return the LED color
   */
  Color8Bit GetLED8Bit(size_t index) const {
    const auto& led = m_buffer.at(index);
    return Color8Bit{led.r, led.g, led.b};
  }

  /**
   * Implicit conversion to span of LED data
   */
  operator std::span<AddressableLED::LEDData>() {
    return std::span<AddressableLED::LEDData>{m_buffer};
  }

  /**
   * Gets the LED data at the specified index.
   *
   * @param index the index
   * @return reference to the LED data
   */
  AddressableLED::LEDData& operator[](size_t index) {
    return m_buffer.at(index);
  }

  /**
   * Gets the LED data at the specified index.
   *
   * @param index the index
   * @return const reference to the LED data
   */
  const AddressableLED::LEDData& operator[](size_t index) const {
    return m_buffer.at(index);
  }

  auto begin() { return m_buffer.begin(); }
  auto end() { return m_buffer.end(); }

 private:
  std::vector<AddressableLED::LEDData> m_buffer;
};

}  // namespace frc
