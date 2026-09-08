project('robotpy-telemetry', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++23',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('semiwrap')

telemetry_sources += files(
    'telemetry/src/main.cpp',
    'telemetry/src/rpy/MockTelemetryBackendFunctions.cpp',
    'telemetry/src/rpy/PyTelemetryTable.cpp',
    'telemetry/src/rpy/TelemetryFunctions.cpp',
)

subdir('semiwrap/modules')
