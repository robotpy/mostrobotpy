project('wpimath-test', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++20',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('wrapcfg')

wpimath_test_sources += files(
    'wpimath_test/src/module.cpp',
)

subdir('wrapcfg/modules')
