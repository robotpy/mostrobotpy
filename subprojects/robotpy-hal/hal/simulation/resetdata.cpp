
#ifndef __FRC_ROBORIO__

#include <hal/simulation/AccelerometerData.h>
#include <hal/simulation/AddressableLEDData.h>
#include <hal/simulation/AnalogGyroData.h>
#include <hal/simulation/AnalogInData.h>
#include <hal/simulation/AnalogOutData.h>
#include <hal/simulation/AnalogTriggerData.h>
#include <hal/simulation/CTREPCMData.h>
#include <hal/simulation/CanData.h>
#include <hal/simulation/DIOData.h>
#include <hal/simulation/DigitalPWMData.h>
#include <hal/simulation/DriverStationData.h>
#include <hal/simulation/DutyCycleData.h>
#include <hal/simulation/EncoderData.h>
#include <hal/simulation/I2CData.h>
#include <hal/simulation/PWMData.h>
#include <hal/simulation/PowerDistributionData.h>
#include <hal/simulation/REVPHData.h>
#include <hal/simulation/RelayData.h>
#include <hal/simulation/RoboRioData.h>
#include <hal/simulation/SPIAccelerometerData.h>
#include <hal/simulation/SPIData.h>
#include <hal/simulation/SimDeviceData.h>

// from PortsInternal.h
constexpr int32_t kNumAccumulators = 2;
constexpr int32_t kNumAnalogTriggers = 8;
constexpr int32_t kNumAnalogInputs = 8;
constexpr int32_t kNumAnalogOutputs = 2;
constexpr int32_t kNumCounters = 8;
constexpr int32_t kNumDigitalHeaders = 10;
constexpr int32_t kNumPWMHeaders = 10;
constexpr int32_t kNumDigitalChannels = 31;
constexpr int32_t kNumPWMChannels = 20;
constexpr int32_t kNumDigitalPWMOutputs = 6;
constexpr int32_t kNumEncoders = 8;
constexpr int32_t kNumInterrupts = 8;
constexpr int32_t kNumRelayChannels = 8;
constexpr int32_t kNumRelayHeaders = kNumRelayChannels / 2;
constexpr int32_t kNumCTREPCMModules = 63;
constexpr int32_t kNumCTRESolenoidChannels = 8;
constexpr int32_t kNumCTREPDPModules = 63;
constexpr int32_t kNumCTREPDPChannels = 16;
constexpr int32_t kNumREVPDHModules = 63;
constexpr int32_t kNumREVPDHChannels = 24;
constexpr int32_t kNumDutyCycles = 8;
constexpr int32_t kNumAddressableLEDs = 1;
constexpr int32_t kNumREVPHModules = 63;
constexpr int32_t kNumREVPHChannels = 16;

// new items
constexpr int32_t kAccelerometers = 1;
constexpr int32_t kI2CPorts = 2;
constexpr int32_t kSPIAccelerometers = 5;
constexpr int32_t kSPIPorts = 5;
constexpr int32_t kNumPDSimModules = kNumREVPDHModules;

void HALSIM_ResetAllData() {
  for (int32_t i = 0; i < kAccelerometers; i++) {
    HALSIM_ResetAccelerometerData(i);
  }

  for (int32_t i = 0; i < kNumAddressableLEDs; i++) {
    HALSIM_ResetAddressableLEDData(i);
  }

  for (int32_t i = 0; i < kNumAccumulators; i++) {
    HALSIM_ResetAnalogGyroData(i);
  }

  for (int32_t i = 0; i < kNumAnalogInputs; i++) {
    HALSIM_ResetAnalogInData(i);
  }

  for (int32_t i = 0; i < kNumAnalogOutputs; i++) {
    HALSIM_ResetAnalogOutData(i);
  }

  for (int32_t i = 0; i < kNumAnalogTriggers; i++) {
    HALSIM_ResetAnalogTriggerData(i);
  }

  HALSIM_ResetCanData();

  for (int32_t i = 0; i < kNumCTREPCMModules; i++) {
    HALSIM_ResetCTREPCMData(i);
  }

  for (int32_t i = 0; i < kNumDigitalPWMOutputs; i++) {
    HALSIM_ResetDigitalPWMData(i);
  }

  for (int32_t i = 0; i < kNumDigitalChannels; i++) {
    HALSIM_ResetDIOData(i);
  }

  HALSIM_ResetDriverStationData();

  for (int32_t i = 0; i < kNumDutyCycles; i++) {
    HALSIM_ResetDutyCycleData(i);
  }

  for (int32_t i = 0; i < kNumEncoders; i++) {
    HALSIM_ResetEncoderData(i);
  }

  for (int32_t i = 0; i < kI2CPorts; i++) {
    HALSIM_ResetI2CData(i);
  }

  for (int32_t i = 0; i < kNumPDSimModules; i++) {
    HALSIM_ResetPowerDistributionData(i);
  }

  for (int32_t i = 0; i < kNumPWMChannels; i++) {
    HALSIM_ResetPWMData(i);
  }

  for (int32_t i = 0; i < kNumRelayHeaders; i++) {
    HALSIM_ResetRelayData(i);
  }

  for (int32_t i = 0; i < kNumREVPHModules; i++) {
    HALSIM_ResetREVPHData(i);
  }

  HALSIM_ResetRoboRioData();
  HALSIM_ResetSimDeviceData();

  for (int32_t i = 0; i < kSPIAccelerometers; i++) {
    HALSIM_ResetSPIAccelerometerData(i);
  }

  for (int32_t i = 0; i < kSPIPorts; i++) {
    HALSIM_ResetSPIData(i);
  }
}

#else

void HALSIM_ResetAllData() {}

#endif