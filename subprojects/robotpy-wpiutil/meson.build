project('robotpy-wpiutil', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++20',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('wrapcfg')

wpiutil_sources += files(
    'wpiutil/src/main.cpp',
    'wpiutil/src/safethread_gil.cpp',
    'wpiutil/src/stacktracehook.cpp',
    'wpiutil/src/wpistruct/wpystruct_fns.cpp',
)

subdir('wrapcfg/modules')
