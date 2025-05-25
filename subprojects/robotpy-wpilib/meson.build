project('wpilib', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++20',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('semiwrap')

wpilib_sources += files(
    'wpilib/src/main.cpp',
    'wpilib/src/rpy/ControlWord.cpp',
    'wpilib/src/rpy/Notifier.cpp',
    'wpilib/src/rpy/SmartDashboardData.cpp',
    'wpilib/src/rpy/MotorControllerGroup.cpp',
)

wpilib_counter_sources += files(
    'wpilib/counter/counter.cpp',
)

wpilib_drive_sources += files(
    'wpilib/drive/drive.cpp',
)

wpilib_event_sources += files(
    'wpilib/event/event.cpp',
)

wpilib_interfaces_sources += files(
    'wpilib/interfaces/interfaces.cpp',
)

wpilib_simulation_sources += files(
    'wpilib/simulation/simulation.cpp',
)

subdir('semiwrap/modules')
