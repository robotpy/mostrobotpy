project('robotpy-hal', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++20',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('semiwrap')

wpihal_sources += files(
    'hal/src/hal.cpp',
)

hal_simulation_sources += files(
    'hal/simulation/main.cpp',
    'hal/simulation/resethandles.cpp',
)

subdir('semiwrap/modules')
