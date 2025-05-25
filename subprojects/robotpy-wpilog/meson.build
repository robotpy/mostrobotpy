project('robotpy-wpilog', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++20',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('semiwrap')

wpilog_sources += files(
    'src/main.cpp',
)

subdir('semiwrap/modules')
