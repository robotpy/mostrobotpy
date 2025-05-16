project('wpimath-test', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++20',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('semiwrap')

wpimath_test_sources += files(
    'wpimath_test/src/module.cpp',
)

subdir('semiwrap/modules')
