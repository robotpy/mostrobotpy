project('robotpy-xrp', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++20',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('semiwrap')

xrp_sources += files(
    'xrp/src/main.cpp',
)

subdir('semiwrap/modules')
