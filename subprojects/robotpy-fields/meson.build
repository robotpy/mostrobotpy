project('robotpy-fields', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++23',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('semiwrap')

fields_sources += files(
    'robotpy_fields/src/main.cpp',
)

subdir('semiwrap/modules')
