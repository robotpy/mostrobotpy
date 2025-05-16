project('pyntcore', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++20',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('semiwrap')

ntcore_sources += files(
    'ntcore/src/ntcore.cpp',
    'ntcore/src/nt_instance.cpp',
    'ntcore/src/py2value.cpp',
    'ntcore/src/pyentry.cpp',
)

subdir('semiwrap/modules')
