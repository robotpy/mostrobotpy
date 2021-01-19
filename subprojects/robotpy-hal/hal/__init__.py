from .version import version as __version__

# Only needed for side effects
from . import _initialize
from .exceptions import HALError

# autogenerated by 'robotpy-build create-imports hal hal._wpiHal'
from ._wpiHal import (
    AccelerometerRange,
    AddressableLEDData,
    AllianceStationID,
    AnalogTriggerType,
    CANDeviceType,
    CANManufacturer,
    CANStreamMessage,
    CAN_CloseStreamSession,
    CAN_GetCANStatus,
    CAN_OpenStreamSession,
    CAN_ReceiveMessage,
    CAN_SendMessage,
    ControlWord,
    CounterMode,
    EncoderEncodingType,
    EncoderIndexingType,
    HandleEnum,
    I2CPort,
    JoystickAxes,
    JoystickButtons,
    JoystickDescriptor,
    JoystickPOVs,
    MatchInfo,
    MatchType,
    RuntimeType,
    SPIPort,
    SerialPort,
    SimBoolean,
    SimDevice,
    SimDouble,
    SimEnum,
    SimInt,
    SimLong,
    SimValue,
    SimValueDirection,
    allocateDigitalPWM,
    calibrateAnalogGyro,
    cancelNotifierAlarm,
    checkAnalogInputChannel,
    checkAnalogModule,
    checkAnalogOutputChannel,
    checkCompressorModule,
    checkDIOChannel,
    checkPDPChannel,
    checkPDPModule,
    checkPWMChannel,
    checkRelayChannel,
    checkSolenoidChannel,
    checkSolenoidModule,
    cleanAnalogTrigger,
    cleanCAN,
    cleanInterrupts,
    cleanNotifier,
    cleanPDP,
    clearAllPCMStickyFaults,
    clearCounterDownSource,
    clearCounterUpSource,
    clearPDPStickyFaults,
    clearSerial,
    closeI2C,
    closeSPI,
    closeSerial,
    configureSPIAutoStall,
    createHandle,
    createPortHandle,
    createPortHandleForSPI,
    createSimDevice,
    createSimValue,
    createSimValueBoolean,
    createSimValueDouble,
    createSimValueEnum,
    disableInterrupts,
    disableSerialTermination,
    enableInterrupts,
    enableSerialTermination,
    exitMain,
    expandFPGATime,
    fireOneShot,
    flushSerial,
    forceSPIAutoRead,
    freeAddressableLED,
    freeAnalogGyro,
    freeAnalogInputPort,
    freeAnalogOutputPort,
    freeCounter,
    freeDIOPort,
    freeDigitalPWM,
    freeDutyCycle,
    freeEncoder,
    freePWMPort,
    freeRelayPort,
    freeSPIAuto,
    freeSimDevice,
    freeSolenoidPort,
    getAccelerometerX,
    getAccelerometerY,
    getAccelerometerZ,
    getAccumulatorCount,
    getAccumulatorOutput,
    getAccumulatorValue,
    getAllSolenoids,
    getAllianceStation,
    getAnalogAverageBits,
    getAnalogAverageValue,
    getAnalogAverageVoltage,
    getAnalogGyroAngle,
    getAnalogGyroCenter,
    getAnalogGyroOffset,
    getAnalogGyroRate,
    getAnalogLSBWeight,
    getAnalogOffset,
    getAnalogOutput,
    getAnalogOversampleBits,
    getAnalogSampleRate,
    getAnalogTriggerFPGAIndex,
    getAnalogTriggerInWindow,
    getAnalogTriggerOutput,
    getAnalogTriggerTriggerState,
    getAnalogValue,
    getAnalogValueToVolts,
    getAnalogVoltage,
    getAnalogVoltsToValue,
    getBrownedOut,
    getCompressor,
    getCompressorClosedLoopControl,
    getCompressorCurrent,
    getCompressorCurrentTooHighFault,
    getCompressorCurrentTooHighStickyFault,
    getCompressorNotConnectedFault,
    getCompressorNotConnectedStickyFault,
    getCompressorPressureSwitch,
    getCompressorShortedFault,
    getCompressorShortedStickyFault,
    getControlWord,
    getCounter,
    getCounterDirection,
    getCounterPeriod,
    getCounterSamplesToAverage,
    getCounterStopped,
    getCurrentThreadPriority,
    getDIO,
    getDIODirection,
    getDutyCycleFPGAIndex,
    getDutyCycleFrequency,
    getDutyCycleOutput,
    getDutyCycleOutputRaw,
    getDutyCycleOutputScaleFactor,
    getEncoder,
    getEncoderDecodingScaleFactor,
    getEncoderDirection,
    getEncoderDistance,
    getEncoderDistancePerPulse,
    getEncoderEncodingScale,
    getEncoderEncodingType,
    getEncoderFPGAIndex,
    getEncoderPeriod,
    getEncoderRate,
    getEncoderRaw,
    getEncoderSamplesToAverage,
    getEncoderStopped,
    getErrorMessage,
    getFPGAButton,
    getFPGARevision,
    getFPGATime,
    getFPGAVersion,
    getFilterPeriod,
    getFilterSelect,
    getHandleIndex,
    getHandleType,
    getHandleTypedIndex,
    getJoystickAxes,
    getJoystickAxisType,
    getJoystickButtons,
    getJoystickDescriptor,
    getJoystickIsXbox,
    getJoystickName,
    getJoystickPOVs,
    getJoystickType,
    getMatchInfo,
    getMatchTime,
    getNumAccumulators,
    getNumAddressableLEDs,
    getNumAnalogInputs,
    getNumAnalogOutputs,
    getNumAnalogTriggers,
    getNumCounters,
    getNumDigitalChannels,
    getNumDigitalHeaders,
    getNumDigitalPWMOutputs,
    getNumDutyCycles,
    getNumEncoders,
    getNumInterrupts,
    getNumPCMModules,
    getNumPDPChannels,
    getNumPDPModules,
    getNumPWMChannels,
    getNumPWMHeaders,
    getNumRelayChannels,
    getNumRelayHeaders,
    getNumSolenoidChannels,
    getPCMSolenoidBlackList,
    getPCMSolenoidVoltageFault,
    getPCMSolenoidVoltageStickyFault,
    getPDPAllChannelCurrents,
    getPDPChannelCurrent,
    getPDPTemperature,
    getPDPTotalCurrent,
    getPDPTotalEnergy,
    getPDPTotalPower,
    getPDPVoltage,
    getPWMConfigRaw,
    getPWMCycleStartTime,
    getPWMEliminateDeadband,
    getPWMLoopTiming,
    getPWMPosition,
    getPWMRaw,
    getPWMSpeed,
    getPort,
    getPortHandleChannel,
    getPortHandleModule,
    getPortHandleSPIEnable,
    getPortWithModule,
    getRelay,
    getRuntimeType,
    getSPIAutoDroppedCount,
    getSPIHandle,
    getSerialBytesReceived,
    getSerialFD,
    getSimValue,
    getSimValueBoolean,
    getSimValueDouble,
    getSimValueEnum,
    getSimValueInt,
    getSimValueLong,
    getSolenoid,
    getSystemActive,
    getSystemClockTicksPerMicrosecond,
    getUserActive3V3,
    getUserActive5V,
    getUserActive6V,
    getUserCurrent3V3,
    getUserCurrent5V,
    getUserCurrent6V,
    getUserCurrentFaults3V3,
    getUserCurrentFaults5V,
    getUserCurrentFaults6V,
    getUserVoltage3V3,
    getUserVoltage5V,
    getUserVoltage6V,
    getVinCurrent,
    getVinVoltage,
    hasMain,
    initAccumulator,
    initSPIAuto,
    initialize,
    initializeAddressableLED,
    initializeAnalogGyro,
    initializeAnalogInputPort,
    initializeAnalogOutputPort,
    initializeAnalogTrigger,
    initializeAnalogTriggerDutyCycle,
    initializeCAN,
    initializeCompressor,
    initializeCounter,
    initializeDIOPort,
    initializeDriverStation,
    initializeDutyCycle,
    initializeEncoder,
    initializeI2C,
    initializeInterrupts,
    initializeNotifier,
    initializePDP,
    initializePWMPort,
    initializeRelayPort,
    initializeSPI,
    initializeSerialPort,
    initializeSerialPortDirect,
    initializeSolenoidPort,
    isAccumulatorChannel,
    isAnyPulsing,
    isHandleCorrectVersion,
    isHandleType,
    isNewControlData,
    isPulsing,
    latchPWMZero,
    observeUserProgramAutonomous,
    observeUserProgramDisabled,
    observeUserProgramStarting,
    observeUserProgramTeleop,
    observeUserProgramTest,
    pulse,
    readCANPacketLatest,
    readCANPacketNew,
    readCANPacketTimeout,
    readI2C,
    readInterruptFallingTimestamp,
    readInterruptRisingTimestamp,
    readSPI,
    readSPIAutoReceivedData,
    readSerial,
    releaseDSMutex,
    releaseWaitingInterrupt,
    report,
    requestInterrupts,
    resetAccumulator,
    resetAnalogGyro,
    resetCounter,
    resetEncoder,
    resetPDPTotalEnergy,
    resetSimValue,
    runMain,
    sendConsoleLine,
    sendError,
    setAccelerometerActive,
    setAccelerometerRange,
    setAccumulatorCenter,
    setAccumulatorDeadband,
    setAddressableLEDBitTiming,
    setAddressableLEDLength,
    setAddressableLEDOutputPort,
    setAddressableLEDSyncTime,
    setAllSolenoids,
    setAnalogAverageBits,
    setAnalogGyroDeadband,
    setAnalogGyroParameters,
    setAnalogGyroVoltsPerDegreePerSecond,
    setAnalogInputSimDevice,
    setAnalogOutput,
    setAnalogOversampleBits,
    setAnalogSampleRate,
    setAnalogTriggerAveraged,
    setAnalogTriggerFiltered,
    setAnalogTriggerLimitsDutyCycle,
    setAnalogTriggerLimitsRaw,
    setAnalogTriggerLimitsVoltage,
    setCompressorClosedLoopControl,
    setCounterAverageSize,
    setCounterDownSource,
    setCounterDownSourceEdge,
    setCounterExternalDirectionMode,
    setCounterMaxPeriod,
    setCounterPulseLengthMode,
    setCounterReverseDirection,
    setCounterSamplesToAverage,
    setCounterSemiPeriodMode,
    setCounterUpDownMode,
    setCounterUpSource,
    setCounterUpSourceEdge,
    setCounterUpdateWhenEmpty,
    setCurrentThreadPriority,
    setDIO,
    setDIODirection,
    setDIOSimDevice,
    setDigitalPWMDutyCycle,
    setDigitalPWMOutputChannel,
    setDigitalPWMRate,
    setEncoderDistancePerPulse,
    setEncoderIndexSource,
    setEncoderMaxPeriod,
    setEncoderMinRate,
    setEncoderReverseDirection,
    setEncoderSamplesToAverage,
    setEncoderSimDevice,
    setFilterPeriod,
    setFilterSelect,
    setInterruptUpSourceEdge,
    setJoystickOutputs,
    setNotifierName,
    setOneShotDuration,
    setPWMConfig,
    setPWMConfigRaw,
    setPWMDisabled,
    setPWMEliminateDeadband,
    setPWMPeriodScale,
    setPWMPosition,
    setPWMRaw,
    setPWMSpeed,
    setRelay,
    setSPIAutoTransmitData,
    setSPIChipSelectActiveHigh,
    setSPIChipSelectActiveLow,
    setSPIHandle,
    setSPIOpts,
    setSPISpeed,
    setSerialBaudRate,
    setSerialDataBits,
    setSerialFlowControl,
    setSerialParity,
    setSerialReadBufferSize,
    setSerialStopBits,
    setSerialTimeout,
    setSerialWriteBufferSize,
    setSerialWriteMode,
    setSimValue,
    setSimValueBoolean,
    setSimValueDouble,
    setSimValueEnum,
    setSimValueInt,
    setSimValueLong,
    setSolenoid,
    setupAnalogGyro,
    shutdown,
    simPeriodicAfter,
    simPeriodicBefore,
    startAddressableLEDOutput,
    startSPIAutoRate,
    startSPIAutoTrigger,
    stopAddressableLEDOutput,
    stopCANPacketRepeating,
    stopNotifier,
    stopSPIAuto,
    tInstances,
    tResourceType,
    transactionI2C,
    transactionSPI,
    updateNotifierAlarm,
    waitForDSData,
    waitForDSDataTimeout,
    waitForInterrupt,
    waitForNotifierAlarm,
    writeAddressableLEDData,
    writeCANPacket,
    writeCANPacketRepeating,
    writeCANRTRFrame,
    writeI2C,
    writeSPI,
    writeSerial,
    __halplatform__,
    __hal_simulation__,
)

__all__ = [
    "AccelerometerRange",
    "AddressableLEDData",
    "AllianceStationID",
    "AnalogTriggerType",
    "CANDeviceType",
    "CANManufacturer",
    "CANStreamMessage",
    "CAN_CloseStreamSession",
    "CAN_GetCANStatus",
    "CAN_OpenStreamSession",
    "CAN_ReceiveMessage",
    "CAN_SendMessage",
    "ControlWord",
    "CounterMode",
    "EncoderEncodingType",
    "EncoderIndexingType",
    "HandleEnum",
    "I2CPort",
    "JoystickAxes",
    "JoystickButtons",
    "JoystickDescriptor",
    "JoystickPOVs",
    "MatchInfo",
    "MatchType",
    "RuntimeType",
    "SPIPort",
    "SerialPort",
    "SimBoolean",
    "SimDevice",
    "SimDouble",
    "SimEnum",
    "SimInt",
    "SimLong",
    "SimValue",
    "SimValueDirection",
    "allocateDigitalPWM",
    "calibrateAnalogGyro",
    "cancelNotifierAlarm",
    "checkAnalogInputChannel",
    "checkAnalogModule",
    "checkAnalogOutputChannel",
    "checkCompressorModule",
    "checkDIOChannel",
    "checkPDPChannel",
    "checkPDPModule",
    "checkPWMChannel",
    "checkRelayChannel",
    "checkSolenoidChannel",
    "checkSolenoidModule",
    "cleanAnalogTrigger",
    "cleanCAN",
    "cleanInterrupts",
    "cleanNotifier",
    "cleanPDP",
    "clearAllPCMStickyFaults",
    "clearCounterDownSource",
    "clearCounterUpSource",
    "clearPDPStickyFaults",
    "clearSerial",
    "closeI2C",
    "closeSPI",
    "closeSerial",
    "configureSPIAutoStall",
    "createHandle",
    "createPortHandle",
    "createPortHandleForSPI",
    "createSimDevice",
    "createSimValue",
    "createSimValueBoolean",
    "createSimValueDouble",
    "createSimValueEnum",
    "disableInterrupts",
    "disableSerialTermination",
    "enableInterrupts",
    "enableSerialTermination",
    "exitMain",
    "expandFPGATime",
    "fireOneShot",
    "flushSerial",
    "forceSPIAutoRead",
    "freeAddressableLED",
    "freeAnalogGyro",
    "freeAnalogInputPort",
    "freeAnalogOutputPort",
    "freeCounter",
    "freeDIOPort",
    "freeDigitalPWM",
    "freeDutyCycle",
    "freeEncoder",
    "freePWMPort",
    "freeRelayPort",
    "freeSPIAuto",
    "freeSimDevice",
    "freeSolenoidPort",
    "getAccelerometerX",
    "getAccelerometerY",
    "getAccelerometerZ",
    "getAccumulatorCount",
    "getAccumulatorOutput",
    "getAccumulatorValue",
    "getAllSolenoids",
    "getAllianceStation",
    "getAnalogAverageBits",
    "getAnalogAverageValue",
    "getAnalogAverageVoltage",
    "getAnalogGyroAngle",
    "getAnalogGyroCenter",
    "getAnalogGyroOffset",
    "getAnalogGyroRate",
    "getAnalogLSBWeight",
    "getAnalogOffset",
    "getAnalogOutput",
    "getAnalogOversampleBits",
    "getAnalogSampleRate",
    "getAnalogTriggerFPGAIndex",
    "getAnalogTriggerInWindow",
    "getAnalogTriggerOutput",
    "getAnalogTriggerTriggerState",
    "getAnalogValue",
    "getAnalogValueToVolts",
    "getAnalogVoltage",
    "getAnalogVoltsToValue",
    "getBrownedOut",
    "getCompressor",
    "getCompressorClosedLoopControl",
    "getCompressorCurrent",
    "getCompressorCurrentTooHighFault",
    "getCompressorCurrentTooHighStickyFault",
    "getCompressorNotConnectedFault",
    "getCompressorNotConnectedStickyFault",
    "getCompressorPressureSwitch",
    "getCompressorShortedFault",
    "getCompressorShortedStickyFault",
    "getControlWord",
    "getCounter",
    "getCounterDirection",
    "getCounterPeriod",
    "getCounterSamplesToAverage",
    "getCounterStopped",
    "getCurrentThreadPriority",
    "getDIO",
    "getDIODirection",
    "getDutyCycleFPGAIndex",
    "getDutyCycleFrequency",
    "getDutyCycleOutput",
    "getDutyCycleOutputRaw",
    "getDutyCycleOutputScaleFactor",
    "getEncoder",
    "getEncoderDecodingScaleFactor",
    "getEncoderDirection",
    "getEncoderDistance",
    "getEncoderDistancePerPulse",
    "getEncoderEncodingScale",
    "getEncoderEncodingType",
    "getEncoderFPGAIndex",
    "getEncoderPeriod",
    "getEncoderRate",
    "getEncoderRaw",
    "getEncoderSamplesToAverage",
    "getEncoderStopped",
    "getErrorMessage",
    "getFPGAButton",
    "getFPGARevision",
    "getFPGATime",
    "getFPGAVersion",
    "getFilterPeriod",
    "getFilterSelect",
    "getHandleIndex",
    "getHandleType",
    "getHandleTypedIndex",
    "getJoystickAxes",
    "getJoystickAxisType",
    "getJoystickButtons",
    "getJoystickDescriptor",
    "getJoystickIsXbox",
    "getJoystickName",
    "getJoystickPOVs",
    "getJoystickType",
    "getMatchInfo",
    "getMatchTime",
    "getNumAccumulators",
    "getNumAddressableLEDs",
    "getNumAnalogInputs",
    "getNumAnalogOutputs",
    "getNumAnalogTriggers",
    "getNumCounters",
    "getNumDigitalChannels",
    "getNumDigitalHeaders",
    "getNumDigitalPWMOutputs",
    "getNumDutyCycles",
    "getNumEncoders",
    "getNumInterrupts",
    "getNumPCMModules",
    "getNumPDPChannels",
    "getNumPDPModules",
    "getNumPWMChannels",
    "getNumPWMHeaders",
    "getNumRelayChannels",
    "getNumRelayHeaders",
    "getNumSolenoidChannels",
    "getPCMSolenoidBlackList",
    "getPCMSolenoidVoltageFault",
    "getPCMSolenoidVoltageStickyFault",
    "getPDPAllChannelCurrents",
    "getPDPChannelCurrent",
    "getPDPTemperature",
    "getPDPTotalCurrent",
    "getPDPTotalEnergy",
    "getPDPTotalPower",
    "getPDPVoltage",
    "getPWMConfigRaw",
    "getPWMCycleStartTime",
    "getPWMEliminateDeadband",
    "getPWMLoopTiming",
    "getPWMPosition",
    "getPWMRaw",
    "getPWMSpeed",
    "getPort",
    "getPortHandleChannel",
    "getPortHandleModule",
    "getPortHandleSPIEnable",
    "getPortWithModule",
    "getRelay",
    "getRuntimeType",
    "getSPIAutoDroppedCount",
    "getSPIHandle",
    "getSerialBytesReceived",
    "getSerialFD",
    "getSimValue",
    "getSimValueBoolean",
    "getSimValueDouble",
    "getSimValueEnum",
    "getSimValueInt",
    "getSimValueLong",
    "getSolenoid",
    "getSystemActive",
    "getSystemClockTicksPerMicrosecond",
    "getUserActive3V3",
    "getUserActive5V",
    "getUserActive6V",
    "getUserCurrent3V3",
    "getUserCurrent5V",
    "getUserCurrent6V",
    "getUserCurrentFaults3V3",
    "getUserCurrentFaults5V",
    "getUserCurrentFaults6V",
    "getUserVoltage3V3",
    "getUserVoltage5V",
    "getUserVoltage6V",
    "getVinCurrent",
    "getVinVoltage",
    "hasMain",
    "initAccumulator",
    "initSPIAuto",
    "initialize",
    "initializeAddressableLED",
    "initializeAnalogGyro",
    "initializeAnalogInputPort",
    "initializeAnalogOutputPort",
    "initializeAnalogTrigger",
    "initializeAnalogTriggerDutyCycle",
    "initializeCAN",
    "initializeCompressor",
    "initializeCounter",
    "initializeDIOPort",
    "initializeDriverStation",
    "initializeDutyCycle",
    "initializeEncoder",
    "initializeI2C",
    "initializeInterrupts",
    "initializeNotifier",
    "initializePDP",
    "initializePWMPort",
    "initializeRelayPort",
    "initializeSPI",
    "initializeSerialPort",
    "initializeSerialPortDirect",
    "initializeSolenoidPort",
    "isAccumulatorChannel",
    "isAnyPulsing",
    "isHandleCorrectVersion",
    "isHandleType",
    "isNewControlData",
    "isPulsing",
    "latchPWMZero",
    "observeUserProgramAutonomous",
    "observeUserProgramDisabled",
    "observeUserProgramStarting",
    "observeUserProgramTeleop",
    "observeUserProgramTest",
    "pulse",
    "readCANPacketLatest",
    "readCANPacketNew",
    "readCANPacketTimeout",
    "readI2C",
    "readInterruptFallingTimestamp",
    "readInterruptRisingTimestamp",
    "readSPI",
    "readSPIAutoReceivedData",
    "readSerial",
    "releaseDSMutex",
    "releaseWaitingInterrupt",
    "report",
    "requestInterrupts",
    "resetAccumulator",
    "resetAnalogGyro",
    "resetCounter",
    "resetEncoder",
    "resetPDPTotalEnergy",
    "resetSimValue",
    "runMain",
    "sendConsoleLine",
    "sendError",
    "setAccelerometerActive",
    "setAccelerometerRange",
    "setAccumulatorCenter",
    "setAccumulatorDeadband",
    "setAddressableLEDBitTiming",
    "setAddressableLEDLength",
    "setAddressableLEDOutputPort",
    "setAddressableLEDSyncTime",
    "setAllSolenoids",
    "setAnalogAverageBits",
    "setAnalogGyroDeadband",
    "setAnalogGyroParameters",
    "setAnalogGyroVoltsPerDegreePerSecond",
    "setAnalogInputSimDevice",
    "setAnalogOutput",
    "setAnalogOversampleBits",
    "setAnalogSampleRate",
    "setAnalogTriggerAveraged",
    "setAnalogTriggerFiltered",
    "setAnalogTriggerLimitsDutyCycle",
    "setAnalogTriggerLimitsRaw",
    "setAnalogTriggerLimitsVoltage",
    "setCompressorClosedLoopControl",
    "setCounterAverageSize",
    "setCounterDownSource",
    "setCounterDownSourceEdge",
    "setCounterExternalDirectionMode",
    "setCounterMaxPeriod",
    "setCounterPulseLengthMode",
    "setCounterReverseDirection",
    "setCounterSamplesToAverage",
    "setCounterSemiPeriodMode",
    "setCounterUpDownMode",
    "setCounterUpSource",
    "setCounterUpSourceEdge",
    "setCounterUpdateWhenEmpty",
    "setCurrentThreadPriority",
    "setDIO",
    "setDIODirection",
    "setDIOSimDevice",
    "setDigitalPWMDutyCycle",
    "setDigitalPWMOutputChannel",
    "setDigitalPWMRate",
    "setEncoderDistancePerPulse",
    "setEncoderIndexSource",
    "setEncoderMaxPeriod",
    "setEncoderMinRate",
    "setEncoderReverseDirection",
    "setEncoderSamplesToAverage",
    "setEncoderSimDevice",
    "setFilterPeriod",
    "setFilterSelect",
    "setInterruptUpSourceEdge",
    "setJoystickOutputs",
    "setNotifierName",
    "setOneShotDuration",
    "setPWMConfig",
    "setPWMConfigRaw",
    "setPWMDisabled",
    "setPWMEliminateDeadband",
    "setPWMPeriodScale",
    "setPWMPosition",
    "setPWMRaw",
    "setPWMSpeed",
    "setRelay",
    "setSPIAutoTransmitData",
    "setSPIChipSelectActiveHigh",
    "setSPIChipSelectActiveLow",
    "setSPIHandle",
    "setSPIOpts",
    "setSPISpeed",
    "setSerialBaudRate",
    "setSerialDataBits",
    "setSerialFlowControl",
    "setSerialParity",
    "setSerialReadBufferSize",
    "setSerialStopBits",
    "setSerialTimeout",
    "setSerialWriteBufferSize",
    "setSerialWriteMode",
    "setSimValue",
    "setSimValueBoolean",
    "setSimValueDouble",
    "setSimValueEnum",
    "setSimValueInt",
    "setSimValueLong",
    "setSolenoid",
    "setupAnalogGyro",
    "shutdown",
    "simPeriodicAfter",
    "simPeriodicBefore",
    "startAddressableLEDOutput",
    "startSPIAutoRate",
    "startSPIAutoTrigger",
    "stopAddressableLEDOutput",
    "stopCANPacketRepeating",
    "stopNotifier",
    "stopSPIAuto",
    "tInstances",
    "tResourceType",
    "transactionI2C",
    "transactionSPI",
    "updateNotifierAlarm",
    "waitForDSData",
    "waitForDSDataTimeout",
    "waitForInterrupt",
    "waitForNotifierAlarm",
    "writeAddressableLEDData",
    "writeCANPacket",
    "writeCANPacketRepeating",
    "writeCANRTRFrame",
    "writeI2C",
    "writeSPI",
    "writeSerial",
]

if __hal_simulation__:
    from ._wpiHal import (
        loadExtensions,
        loadOneExtension,
        setDutyCycleSimDevice,
        setShowExtensionsNotFoundMessages,
    )

    __all__ += [
        "loadExtensions",
        "loadOneExtension",
        "setDutyCycleSimDevice",
        "setShowExtensionsNotFoundMessages",
    ]
