project('robotpy-telemetry', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++23',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('semiwrap')

telemetry_sources += files(
    'telemetry/src/main.cpp',
    'telemetry/src/TelemetryPython.cpp',
)

subdir('semiwrap/modules')
