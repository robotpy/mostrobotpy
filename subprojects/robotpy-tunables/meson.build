project('robotpy-tunables', ['cpp'],
        default_options: ['warning_level=1', 'cpp_std=c++23',
                          'b_colorout=auto', 'optimization=2', 'b_pie=true'])

subdir('semiwrap')

tunables_sources += files(
    'tunables/src/main.cpp',
    'tunables/src/TunablePython.cpp',
)

subdir('semiwrap/modules')
